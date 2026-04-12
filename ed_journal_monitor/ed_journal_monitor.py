import logging
import os
import re
import time
from datetime import datetime
from operator import itemgetter
from pathlib import Path

import zmq
from watchdog.events import (FileSystemEvent, 
                             RegexMatchingEventHandler)
from watchdog.observers import Observer

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

JOURNALS_PATH = Path.home() / "Saved Games" / "Frontier Developments" / "Elite Dangerous"
# Journal.YYYY-MM-DDTHH-MM-SS.XX.log - Odyssey logs format
JOURNAL_REGEX = (r".*Journal\."
                 r"(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})"
                 r"T(?P<hour>\d{2})(?P<minute>\d{2})(?P<second>\d{2})"
                 r"\.(?P<part>\d{2})\.log$")
JOURNAL_REGEX_PATTERN = re.compile(JOURNAL_REGEX)


def _to_stamp(match_dict: dict[str, str]) -> tuple[datetime, int]:
    """
    Utility function to obtain a tuple of datetime and part number from 
    the regex match dictionary.

    :param match_dict: Match dictionary retrieved by matching against 
    JOURNAL_REGEX 
    :return: tuple of datetime and part number
    """
    dict_ = {key: int(value) for key, value in match_dict.items()}
    part = dict_.pop("part")
    return datetime(**dict_), part


def _get_latest_journal(journals_path: Path) -> Path:
    """
    Finds the latest journal on the given path.

    :param journals_path: path to the directory containing journal files
    :return: Journal object corresponding to the latest journal
    """
    all_paths = journals_path.iterdir()
    paths_and_stamps = (
        (path, _to_stamp(match.groupdict())) 
        for path in all_paths
        if (match := JOURNAL_REGEX_PATTERN.match(path.name)) is not None) 
    latest_journal, _ = max(paths_and_stamps, 
                            key=itemgetter(1),
                            default=(None, None))
    if latest_journal is None:
        raise ValueError(f"Couldn't find any journals in {journals_path}")
    return latest_journal


class JournalHandler(RegexMatchingEventHandler):
    """
    Custom event handler for journal files, extending 
    RegexMatchingEventHandler from the watchdog library.
    """
    def __init__(self) -> None:
        super().__init__(regexes=[JOURNAL_REGEX], 
                         ignore_regexes=[], 
                         ignore_directories=True, 
                         case_sensitive=True)
        """
        Initialize the JournalHandler by opening the latest journal and 
        setting up the ZeroMQ publisher socket.
        """
        latest_journal_path = _get_latest_journal(JOURNALS_PATH)
        self.latest_journal = open(latest_journal_path)
        self.latest_journal.seek(0, os.SEEK_END)
        logger.info(f"Opened latest journal: {latest_journal_path}")
        ctx = zmq.Context()
        self.sock = ctx.socket(zmq.PUB)
        self.sock.bind("tcp://127.0.0.1:5555")

    def on_any_event(self, event: FileSystemEvent) -> None:
        """Overrides the default FileSystemEventHandler.on_any_event."""
        if event.src_path != self.latest_journal.name:
            # This can happen when the monitor is started before the game
            logger.info(f"Received a non-'on-created' event but the "
                        f"path doesn't match: {event.src_path}")
            self.switch_journal(event.src_path)
        logger.info(f"EVENT: {event.event_type} - {event.src_path}")

    def on_created(self, event: FileSystemEvent) -> None:
        """Overrides the default FileSystemEventHandler.on_created."""
        logger.info(f"New journal created: {event.src_path}")
        self.switch_journal(event.src_path)

    def on_modified(self, event: FileSystemEvent) -> None:
        """Overrides the default FileSystemEventHandler.on_modified."""
        logger.debug(f"File modified: {event.src_path}")
        self.read_lines()

    def switch_journal(self, new_journal_path: bytes | str) -> None:
        """
        Utility method to switch the currently opened journal to a new one.

        :param new_journal_path: path to the new journal file
        """
        logger.info(f"Switching to new journal: {new_journal_path}")
        self.latest_journal.close()
        self.latest_journal = open(new_journal_path)
        self.read_lines()

    def read_lines(self) -> None:
        """
        This method does not override any default method, 
        it is used to read new lines from the currently opened journal 
        and publish them to the ZeroMQ socket.
        """
        while True:
            line = self.latest_journal.readline()
            if not line:
                break
            clean_line = line.rstrip("\n")
            logger.debug(f"Read line: {clean_line}")
            self.sock.send_string(clean_line)
            logger.debug("Line published")


# Logic according to 
# https://pythonhosted.org/watchdog/quickstart.html#a-simple-example
if __name__ == "__main__":
    observer = Observer()
    observer.schedule(event_handler=JournalHandler(),
                      path=str(JOURNALS_PATH),
                      recursive=True)
    observer.start()
    logger.info("Observer started")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down observer")
        observer.stop()

    observer.join()
