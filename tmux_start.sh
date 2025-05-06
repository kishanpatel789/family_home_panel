#!/bin/sh

# set session name
SESSION="panel"
SESSIONEXISTS=$(tmux list-sessions | grep $SESSION)

# only create tmux session if it doesn't already exist
if [ "$SESSIONEXISTS" = "" ]
then
    # start new session
    tmux new-session -d -s $SESSION

    # create windows
    tmux rename-window -t 1 'notes'
    tmux send-keys -t 'notes' 'vim notes.md' C-m 

    tmux new-window -t $SESSION:2 -n 'run_debug'
    tmux send-keys -t 'run_debug' 'source venv/bin/activate' C-m 'clear' C-m 'flask run --debug' C-m

    tmux new-window -t $SESSION:3 -n 'code'
    tmux send-keys -t 'code' 'source venv/bin/activate' C-m 'clear' C-m

fi

# attach session, on the main window
tmux attach-session -t $SESSION:1
