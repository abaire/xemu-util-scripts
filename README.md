Some random scripts I use to automate tasks while working on xemu.

* run.sh - Runs the development binary of xemu, including setting DYLD_FALLBACK_LIBRARY_PATH to allow macOS bundled libs to be discovered.
* rebuild.sh - Reconfigures/rebuilds xemu from the commandline.
* update_debug_branches.sh - Rebases the debug/* branches in https://github.com/abaire/xemu onto master
* update_work_branch.sh - Updates the work branch to include the debug/* branches from https://github.com/abaire/xemu

