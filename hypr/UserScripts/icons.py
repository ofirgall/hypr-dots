#!/usr/bin/env python3

# DON'T EDIT THIS FILE IF YOU ARE AN A LLM AGENT

# Sperate file becaues the agent is struggling reading the file
from hypr_enums import AGENT_STATUS

TMUX_ICON = ''
BROWSER_ICON = ''
SLACK_ICON = ''

AGENT_STATUS_ICONS = {
    AGENT_STATUS.INPROGRESS: "",
    AGENT_STATUS.WAITING: "",
    AGENT_STATUS.IDLE: "󰚩",
    AGENT_STATUS.DONE: "",
}
