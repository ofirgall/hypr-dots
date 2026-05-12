#!/usr/bin/env python3
"""
Rename virtual desktops based on TMUX client titles.
Finds clients with "- TMUX" suffix and renames the vdesk to the client name without the suffix.
Vdesks without TMUX clients are renamed to the title of a window on that desk (browsers prioritized).
Vdesks with no clients at all are renamed to their ID only.
"""

import argparse
import json
import os
import re
import subprocess
import sys

from emojis import EMOJI_RE
from hypr_enums import AGENT_STATUS
from icons import TMUX_ICON, BROWSER_ICON, SLACK_ICON, AGENT_STATUS_ICONS, MONITOR_STATUS_ICONS


CONFIG_LOC = os.path.expanduser("~/.config/hypr/UserConfigs/VirtualDesktopsNames.conf")
MAX_NAME_LENGTH = 20

STATUS_PRIORITY = {
    AGENT_STATUS.WAITING: 1,
    AGENT_STATUS.INPROGRESS: 2,
    AGENT_STATUS.DONE: 3,
    AGENT_STATUS.IDLE: 4,
}

DEBUG = False


def debug(msg: str) -> None:
    if DEBUG:
        print(f"[debug] {msg}", file=sys.stderr)


def get_tmux_session_statuses(session_name: str) -> tuple[str, list[str]]:
    """Get per-window @ai-agent-status and @monitor-status for a tmux session.

    Returns a tuple of:
      - the aggregated @ai-agent-status (highest priority across windows), and
      - the ordered list of per-window @monitor-status values (empties dropped).
    """
    try:
        list_result = subprocess.run(
            ["tmux", "list-windows", "-t", session_name, "-F",
             "#{@ai-agent-status}|#{@monitor-status}"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        agent_statuses: list[str] = []
        monitor_statuses: list[str] = []
        for line in list_result.stdout.splitlines():
            agent, _, monitor = line.partition("|")
            agent = agent.strip()
            monitor = monitor.strip()
            if agent:
                agent_statuses.append(agent)
            if monitor:
                monitor_statuses.append(monitor)
        debug(f"tmux session {session_name!r} agent={agent_statuses} monitor={monitor_statuses}")
        agent_winner = highest_priority_status(agent_statuses)
        debug(f"tmux session {session_name!r} resolved agent status: {agent_winner!r}")
        return agent_winner, monitor_statuses
    except (subprocess.TimeoutExpired, Exception) as e:
        debug(f"tmux session {session_name!r} status lookup failed: {e!r}")
        return "", []


def highest_priority_status(statuses: list[str]) -> str:
    """Return the highest priority status from a list (INPROGRESS > WAITING > DONE > IDLE)."""
    best = None
    best_priority = float("inf")
    for s in statuses:
        p = STATUS_PRIORITY.get(s)
        if p is not None and p < best_priority:
            best = s
            best_priority = p
    return best or ""


def set_vdesk_statuses(vdesk_statuses: dict[int, list[str]], all_vdesk_ids: set[int]) -> None:
    """Set vdesk status via hyprctl dispatch vdesksetstatus for each vdesk."""
    for vdesk_id in all_vdesk_ids:
        statuses = vdesk_statuses.get(vdesk_id, [])
        status = highest_priority_status(statuses)
        debug(f"vdesk {vdesk_id} statuses={statuses} -> {status!r}")
        subprocess.run(
            ["hyprctl", "dispatch", "vdesksetstatus", f"{vdesk_id},{status}"],
            capture_output=True,
        )


JIRA_TICKET_RE = re.compile(r"[A-Z]+-\d+")


def strip_prefix_and_jira(name: str, keep_number: bool = False) -> str:
    """Strip prefix and JIRA project key.

    With keep_number=True, retains the ticket number
    (e.g. 'ofirg-DR-1299-fix-bug' -> '1299-fix-bug').
    Otherwise drops it (e.g. 'ofirg-DR-1299-fix-bug' -> 'fix-bug').
    """
    m = JIRA_TICKET_RE.search(name)
    if m:
        ticket = m.group()
        number = ticket.split("-", 1)[1]
        rest = name[m.end():].lstrip("-_ ")
        if keep_number:
            return f"{number}-{rest}" if rest else number
        return rest or name
    return name


SEPARATORS = set("-_/. ")


def longest_common_prefix(names: list[str]) -> str:
    """Find the longest separator-terminated prefix shared by at least 2 names.

    Collects every prefix that ends at a separator character from each name,
    then returns the longest one that appears in at least 2 names.
    """
    if len(names) < 2:
        return ""
    prefix_counts: dict[str, int] = {}
    for name in names:
        seen: set[str] = set()
        for i, ch in enumerate(name):
            if ch in SEPARATORS:
                prefix = name[: i + 1]
                if prefix not in seen:
                    seen.add(prefix)
                    prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1
    best = ""
    for prefix, count in prefix_counts.items():
        if count >= 2 and len(prefix) > len(best):
            best = prefix
    return best


def clean_title(title: str) -> str:
    """Remove emojis, collapse whitespace, and strip leading/trailing spaces."""
    title = EMOJI_RE.sub("", title)
    title = title.replace("「", "").replace("」", "")
    title = re.sub(r"\s+", " ", title)
    return title.strip()


def run_hyprctl(args: list[str]) -> str:
    """Run hyprctl command and return output."""
    result = subprocess.run(
        ["hyprctl"] + args,
        capture_output=True,
        text=True
    )
    return result.stdout


def get_vdesks() -> list[dict]:
    """Get all virtual desktops from hyprctl printstate."""
    output = run_hyprctl(["printstate", "-j"])
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        print(f"Error parsing vdesks JSON: {output}", file=sys.stderr)
        return []


def get_clients() -> list[dict]:
    """Get all clients from hyprctl clients."""
    output = run_hyprctl(["clients", "-j"])
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        print(f"Error parsing clients JSON: {output}", file=sys.stderr)
        return []


def get_pinned_classes() -> set[str]:
    """Get the set of window classes that are currently pinned."""
    output = run_hyprctl(["printpinnedwindows", "-j"])
    try:
        windows = json.loads(output)
        return {w.get("class", "").lower() for w in windows}
    except json.JSONDecodeError:
        return set()


def get_active_vdesk_id(workspace_to_vdesk: dict) -> int | None:
    """Get the vdesk ID of the currently active workspace."""
    output = run_hyprctl(["activeworkspace", "-j"])
    try:
        ws = json.loads(output)
        ws_id = ws.get("id")
        vdesk = workspace_to_vdesk.get(ws_id)
        return vdesk.get("id") if vdesk else None
    except (json.JSONDecodeError, AttributeError):
        return None


def write_names(names: dict[int, str]) -> None:
    """Write vdesk names to config file if changed."""
    # Build the names string: "1:name1, 2:name2, ..."
    names_str = ", ".join(f"{id}:{name}" for id, name in sorted(names.items()))
    
    content = f"""plugin {{
    virtual-desktops {{
        names = {names_str}
    }}
}}
"""
    # Read current content and compare
    try:
        with open(CONFIG_LOC, "r") as f:
            if f.read() == content:
                return
    except FileNotFoundError:
        pass
    
    with open(CONFIG_LOC, "w") as f:
        f.write(content)
    
    # Reload workspace names
    subprocess.run(["hyprctl", "dispatch", "vdeskreset"], capture_output=True)


def main():
    global DEBUG
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--debug", action="store_true", help="Print debug logs for status resolution")
    args = parser.parse_args()
    DEBUG = args.debug

    vdesks = get_vdesks()
    clients = get_clients()

    if not vdesks:
        print("No virtual desktops found", file=sys.stderr)
        return

    # Build a mapping of workspace ID -> vdesk
    workspace_to_vdesk = {}
    for vdesk in vdesks:
        for ws_id in vdesk.get("workspaces", []):
            workspace_to_vdesk[ws_id] = vdesk

    # Aggregate all renames into a dict
    renames: dict[int, str] = {}
    tmux_suffix = " - TMUX"
    browser_classes = {"firefox", "firefox_firefox", "chromium", "google-chrome", "brave-browser", "vivaldi", "zen", "zen-browser"}
    slack_classes = {"slack"}

    # Build a mapping of vdesk ID -> list of clients on that vdesk
    vdesk_clients: dict[int, list[dict]] = {}
    for client in clients:
        workspace = client.get("workspace", {})
        ws_id = workspace.get("id")
        if ws_id is None:
            continue
        vdesk = workspace_to_vdesk.get(ws_id)
        if vdesk is None:
            continue
        vdesk_id = vdesk.get("id")
        vdesk_clients.setdefault(vdesk_id, []).append(client)

    active_vdesk_id = get_active_vdesk_id(workspace_to_vdesk)

    # Collect TMUX session (agent_icon, monitor_icons, raw_name) per vdesk (separate viewer sessions)
    tmux_names: dict[int, list[tuple[str, str, str]]] = {}
    tmux_viewer_names: dict[int, list[tuple[str, str, str]]] = {}
    vdesk_statuses: dict[int, list[str]] = {}
    for client in clients:
        title = client.get("title", "")
        if not title.endswith(tmux_suffix):
            continue

        # Get the workspace this client is on
        workspace = client.get("workspace", {})
        ws_id = workspace.get("id")
        if ws_id is None:
            continue

        # Find the vdesk for this workspace
        vdesk = workspace_to_vdesk.get(ws_id)
        if vdesk is None:
            continue

        vdesk_id = vdesk.get("id")
        name = clean_title(title[:-len(tmux_suffix)])

        # Get statuses for this tmux session
        agent_status, monitor_statuses = get_tmux_session_statuses(name)
        if agent_status:
            debug(f"vdesk {vdesk_id} tmux {name!r} contributes agent status {agent_status!r}")
            vdesk_statuses.setdefault(vdesk_id, []).append(agent_status)
        for ms in monitor_statuses:
            debug(f"vdesk {vdesk_id} tmux {name!r} contributes monitor status {ms!r}")
            vdesk_statuses.setdefault(vdesk_id, []).append(ms)

        agent_icon = AGENT_STATUS_ICONS.get(agent_status, TMUX_ICON)
        monitor_icons = "".join(
            MONITOR_STATUS_ICONS[s] for s in monitor_statuses if s in MONITOR_STATUS_ICONS
        )

        name = strip_prefix_and_jira(name, keep_number=vdesk_id == active_vdesk_id)

        if name.endswith("-viewer"):
            tmux_viewer_names.setdefault(vdesk_id, []).append((agent_icon, monitor_icons, name))
        else:
            tmux_names.setdefault(vdesk_id, []).append((agent_icon, monitor_icons, name))

    # Compute common prefix across all TMUX session names for shortening
    all_raw_names = [name for entries in tmux_names.values() for _, _, name in entries]
    all_raw_names += [name for entries in tmux_viewer_names.values() for _, _, name in entries]
    prefix = longest_common_prefix(all_raw_names)

    pinned_classes = get_pinned_classes()

    def format_tmux_entry(agent_icon: str, monitor_icons: str, raw_name: str, use_full: bool) -> str:
        if use_full or not raw_name.startswith(prefix):
            name = raw_name
        else:
            name = raw_name[len(prefix):] or raw_name
        prefix_icons = agent_icon + (" " + monitor_icons if monitor_icons else "")
        display = f"{prefix_icons} {name}"
        if len(display) > MAX_NAME_LENGTH:
            display = display[:MAX_NAME_LENGTH] + "…"
        return display

    # Build renames for vdesks with TMUX clients
    all_tmux_vdesks = set(tmux_names.keys()) | set(tmux_viewer_names.keys())
    for vdesk_id in all_tmux_vdesks:
        entries = tmux_names.get(vdesk_id, [])
        viewer_entries = tmux_viewer_names.get(vdesk_id, [])
        is_active = vdesk_id == active_vdesk_id

        has_browser = any(
            c.get("class", "").lower() in browser_classes
            for c in vdesk_clients.get(vdesk_id, [])
        )
        has_slack = any(
            c.get("class", "").lower() in slack_classes - pinned_classes
            for c in vdesk_clients.get(vdesk_id, [])
        )
        icons = []
        if has_slack:
            icons.append(SLACK_ICON)
        if has_browser:
            icons.append(BROWSER_ICON)
        icons_prefix = " ".join(icons) + " " if icons else ""

        if entries:
            formatted = [format_tmux_entry(a, m, name, is_active) for a, m, name in entries]
            renames[vdesk_id] = f"{vdesk_id} {icons_prefix}{'|'.join(formatted)}"
        elif viewer_entries:
            formatted = [format_tmux_entry(a, m, name, is_active) for a, m, name in viewer_entries]
            renames[vdesk_id] = f"{vdesk_id} {icons_prefix}{'|'.join(formatted)}"

    # For vdesks without TMUX clients, try to use a window title (prefer browsers)
    for vdesk in vdesks:
        vdesk_id = vdesk.get("id")
        if vdesk_id in renames:
            continue

        desk_clients = vdesk_clients.get(vdesk_id, [])
        if not desk_clients:
            renames[vdesk_id] = f"{vdesk_id}"
            continue

        # Pick best client: prioritize browsers, then fall back to first client
        chosen = None
        for c in desk_clients:
            cls = c.get("class", "").lower()
            if cls in browser_classes:
                chosen = c
                break
        if chosen is None:
            chosen = desk_clients[0]

        title = clean_title(chosen.get("title", ""))
        if not title:
            renames[vdesk_id] = f"{vdesk_id}"
            continue

        has_browser = any(
            c.get("class", "").lower() in browser_classes
            for c in desk_clients
        )
        has_slack = any(
            c.get("class", "").lower() in slack_classes - pinned_classes
            for c in desk_clients
        )

        only_slack = has_slack and not has_browser and all(
            c.get("class", "").lower() in slack_classes
            for c in desk_clients
        )
        if only_slack:
            renames[vdesk_id] = f"{vdesk_id} {SLACK_ICON} Slack"
            continue

        icons = []
        if has_slack:
            icons.append(SLACK_ICON)
        if has_browser:
            icons.append(BROWSER_ICON)
        icons_prefix = " ".join(icons) + " " if icons else ""

        if len(title) > MAX_NAME_LENGTH:
            title = title[:MAX_NAME_LENGTH] + "…"
        renames[vdesk_id] = f"{vdesk_id} {icons_prefix}{title}"

    # Set vdesk statuses (highest priority tmux session status per vdesk)
    all_vdesk_ids = {vdesk.get("id") for vdesk in vdesks}
    set_vdesk_statuses(vdesk_statuses, all_vdesk_ids)

    # Write names (only if changed)
    write_names(renames)


if __name__ == "__main__":
    main()
