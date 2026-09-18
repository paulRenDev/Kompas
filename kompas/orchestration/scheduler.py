"""Scheduler voor Kompas cycli.

Beheert de tijdgebaseerde uitvoering van:
- Pijler A cycli (09:00 en 18:00 CEST)
- Pijler B cycli (09:00 en 18:00 CEST, of vaker)
- Synthese cycli (na Pijler A en B)

De scheduler:
- Gebruikt cron-achtige scheduling
- Houdt rekening met CEST tijdzone
- Beheert overlappinge uitvoeringen
- Logt alle activiteit

Belangrijke principes:
- Pijler A en B draaien gelijktijdig (niet gestaggerd)
- Synthese draait NA Pijler A en B
- Geen cyclus start als de vorige nog draait
- Alle tijden zijn in CEST (UTC+2 in zomer, UTC+1 in winter)
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, time as dt_time, timezone, timedelta
from enum import Enum
from typing import Callable, Optional

# CEST tijdzone (UTC+2 in zomer, UTC+1 in winter)
# We gebruiken een vaste offset voor nu (geen DST handling)
CEST_OFFSET = timedelta(hours=2)


class CycleType(Enum):
    """Type cyclus die gescheduld kan worden."""
    PIJLER_A = "pijler_a"
    PIJLER_B = "pijler_b"
    SYNTHESE = "synthese"
    FULL = "full"  # Pijler A + Pijler B + Synthese


class ScheduleTime(Enum):
    """Standaard schedule tijden voor Kompas."""
    MORNING = dt_time(9, 0)   # 09:00 CEST
    EVENING = dt_time(18, 0)  # 18:00 CEST


@dataclass
class ScheduleConfig:
    """Configuratie voor een schedule."""
    
    # Welke cycli moeten draaien
    cycle_types: list[CycleType] = field(default_factory=list)
    
    # Tijden (in CEST)
    times: list[dt_time] = field(default_factory=list)
    
    # Tijdzone offset
    timezone_offset: timedelta = CEST_OFFSET
    
    # Moet elke dag draaien
    every_day: bool = True
    
    # Dagen van de week (0=maandag, 6=zondag)
    days_of_week: list[int] = field(default_factory=lambda: list(range(7)))
    
    # Actief
    enabled: bool = True


@dataclass
class ScheduledJob:
    """Een geschedulde job."""
    
    name: str
    cycle_type: CycleType
    scheduled_time: datetime
    next_run: datetime
    interval: Optional[timedelta] = None
    callback: Optional[Callable] = None
    is_running: bool = False
    last_run: Optional[datetime] = None
    last_success: Optional[datetime] = None
    last_error: Optional[str] = None
    run_count: int = 0


@dataclass
class SchedulerState:
    """State van de scheduler."""
    
    jobs: list[ScheduledJob] = field(default_factory=list)
    is_running: bool = False
    started_at: Optional[datetime] = None
    last_check: Optional[datetime] = None


class Scheduler:
    """Hoofd scheduler voor Kompas cycli.
    
    Deze klasse beheert:
    - Het plannen van cycli op specifieke tijden
    - Het uitvoeren van cycli op het juiste moment
    - Het bijhouden van state en logging
    - Het voorkomen van overlappinge uitvoeringen
    """
    
    def __init__(self, config: Optional[ScheduleConfig] = None):
        """Initialiseert de scheduler.
        
        Args:
            config: Optionele configuratie. Als None, wordt de
                   standaard configuratie gebruikt (09:00 en 18:00 CEST).
        """
        self.config = config or ScheduleConfig(
            cycle_types=[CycleType.FULL],
            times=[ScheduleTime.MORNING, ScheduleTime.EVENING],
            timezone_offset=CEST_OFFSET,
            every_day=True,
            days_of_week=list(range(7)),
            enabled=True,
        )
        
        self.state = SchedulerState()
        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        
        # Creer de jobs
        self._create_jobs()
    
    def _create_jobs(self):
        """Creert de scheduled jobs gebaseerd op de configuratie."""
        self.state.jobs = []
        
        for cycle_type in self.config.cycle_types:
            for schedule_time in self.config.times:
                # Bereken de volgende run tijd
                next_run = self._calculate_next_run(schedule_time)
                
                job = ScheduledJob(
                    name=f"{cycle_type.value}_{schedule_time.hour}:{schedule_time.minute:02d}",
                    cycle_type=cycle_type,
                    scheduled_time=datetime.combine(
                        datetime.now().date(),
                        schedule_time
                    ),
                    next_run=next_run,
                    callback=None,
                )
                self.state.jobs.append(job)
    
    def _calculate_next_run(self, schedule_time: dt_time) -> datetime:
        """Bereken de volgende run tijd voor een schedule.
        
        Args:
            schedule_time: De geplande tijd (in CEST)
            
        Returns:
            De volgende datetime waarop de job moet draaien
        """
        now = datetime.now(timezone.utc)
        
        # Converteer schedule_time naar UTC
        # schedule_time is in CEST, dus we moeten CEST_OFFSET aftrekken
        # om UTC tijd te krijgen
        utc_time = (datetime.combine(now.date(), schedule_time) - self.config.timezone_offset)
        
        # Als de utc_time al voorbij is vandaag, gebruik dan morgen
        if utc_time < now:
            utc_time = utc_time + timedelta(days=1)
        
        return utc_time
    
    def _should_run_today(self) -> bool:
        """Controleert of er vandaag cycli moeten draaien."""
        if self.config.every_day:
            return True
        
        today = datetime.now(timezone.utc).weekday()
        return today in self.config.days_of_week
    
    def start(self):
        """Start de scheduler.
        
        Deze methode start een achtergrond thread die:
        1. Elke minuut checkt of er jobs moeten draaien
        2. Jobs uitvoert op het juiste moment
        3. State bijhoudt en logt
        """
        if self.state.is_running:
            self.logger.warning("Scheduler is al gestart")
            return
        
        self.state.is_running = True
        self.state.started_at = datetime.now(timezone.utc)
        self.logger.info("Scheduler gestart")
        
        # Start de scheduler thread
        self._thread = threading.Thread(
            target=self._run_loop,
            daemon=True,
            name="Kompas-Scheduler"
        )
        self._thread.start()
    
    def stop(self):
        """Stop de scheduler."""
        self._stop_event.set()
        self.state.is_running = False
        self.logger.info("Scheduler gestopt")
    
    def _run_loop(self):
        """De hoofd loop van de scheduler."""
        while not self._stop_event.is_set():
            try:
                self._check_jobs()
                self.state.last_check = datetime.now(timezone.utc)
                
                # Slaap voor 1 minuut
                time.sleep(60)
                
            except Exception as e:
                self.logger.error(f"Fout in scheduler loop: {e}")
                time.sleep(60)  # Wacht 1 minuut voor herstel
    
    def _check_jobs(self):
        """Controleert alle jobs en voert ze uit als nodig."""
        now = datetime.now(timezone.utc)
        
        if not self._should_run_today():
            return
        
        for job in self.state.jobs:
            if job.is_running:
                # Job is al aan het draaien
                continue
            
            if now >= job.next_run:
                # Tijd om de job uit te voeren
                self._execute_job(job)
    
    def _execute_job(self, job: ScheduledJob):
        """Voert een job uit."""
        with self._lock:
            if job.is_running:
                return
            
            job.is_running = True
            job.last_run = datetime.now(timezone.utc)
        
        try:
            self.logger.info(f"Start job: {job.name}")
            
            # Voer de cyclus uit
            if job.callback:
                job.callback(job)
            else:
                # Standaard: voer de full cycle uit
                from kompas.orchestration.cycle_runner import run_full_cycle
                result = run_full_cycle()
                self.logger.info(f"Job {job.name} voltooid: {result}")
                job.last_success = datetime.now(timezone.utc)
            
            job.run_count += 1
            
            # Bereken de volgende run tijd
            job.next_run = self._calculate_next_run(
                job.scheduled_time.time()
            )
            
        except Exception as e:
            self.logger.error(f"Fout in job {job.name}: {e}")
            job.last_error = str(e)
            
            # Probeer morgen opnieuw
            job.next_run = datetime.now(timezone.utc) + timedelta(days=1)
            
        finally:
            with self._lock:
                job.is_running = False
    
    def add_job(
        self,
        name: str,
        cycle_type: CycleType,
        schedule_time: dt_time,
        callback: Optional[Callable] = None,
    ):
        """Voegt een nieuwe job toe.
        
        Args:
            name: Naam van de job
            cycle_type: Type cyclus
            schedule_time: Tijd (in CEST) waarop de job moet draaien
            callback: Optionele callback functie
        """
        next_run = self._calculate_next_run(schedule_time)
        
        job = ScheduledJob(
            name=name,
            cycle_type=cycle_type,
            scheduled_time=datetime.combine(
                datetime.now().date(),
                schedule_time
            ),
            next_run=next_run,
            callback=callback,
        )
        
        with self._lock:
            self.state.jobs.append(job)
        
        self.logger.info(f"Job toegevoegd: {name}")
        return job
    
    def remove_job(self, name: str) -> bool:
        """Verwijderd een job.
        
        Args:
            name: Naam van de job
            
        Returns:
            True als de job is verwijderd, False als niet gevonden
        """
        with self._lock:
            for i, job in enumerate(self.state.jobs):
                if job.name == name:
                    self.state.jobs.pop(i)
                    self.logger.info(f"Job verwijderd: {name}")
                    return True
        
        return False
    
    def get_next_run(self) -> Optional[datetime]:
        """Geeft de volgende geplande run tijd.
        
        Returns:
            De volgende datetime waarop een job draait, of None
        """
        with self._lock:
            if not self.state.jobs:
                return None
            
            next_runs = [job.next_run for job in self.state.jobs]
            return min(next_runs)
    
    def get_state(self) -> SchedulerState:
        """Geeft de huidige state van de scheduler."""
        with self._lock:
            return self.state


# ============================================================================
# Convenience functies
# ============================================================================

# Globale scheduler instance
_scheduler: Optional[Scheduler] = None


def get_scheduler() -> Scheduler:
    """Geeft de globale scheduler instance.
    
    Returns:
        De scheduler, of creert er een als deze nog niet bestaat
    """
    global _scheduler
    if _scheduler is None:
        _scheduler = Scheduler()
    return _scheduler


def start_scheduler():
    """Start de globale scheduler."""
    get_scheduler().start()


def stop_scheduler():
    """Stop de globale scheduler."""
    get_scheduler().stop()


def run_scheduled_cycles():
    """Start de scheduler en draai de geplande cycli.
    
    Dit is de hoofd functie om te starten desde de command line:
    
        python -m kompas.orchestration.scheduler
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    scheduler = get_scheduler()
    scheduler.start()
    
    # Blijf draaien tot onderbroken
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.stop()


if __name__ == "__main__":
    run_scheduled_cycles()
