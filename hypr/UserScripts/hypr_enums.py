#!/usr/bin/env python3

from enum import StrEnum


class AGENT_STATUS(StrEnum):
    INPROGRESS = "INPROGRESS"
    WAITING = "WAITING"
    IDLE = "IDLE"
