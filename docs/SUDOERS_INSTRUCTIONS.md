SUDOers configuration for non-interactive web erases
===============================================

If you want the web UI to run destructive erases without prompting for a sudo password,
you must add a restricted NOPASSWD sudoers rule for the wrapper script. Use `visudo`
to edit `/etc/sudoers` safely.

1) Open visudo as root (do not edit /etc/sudoers directly):

   sudo visudo

2) Add a single-line rule replacing `www-data` with the user your web server runs as
   (for example `www-data`, `nginx`, or a custom service account):

   www-data ALL=(ALL) NOPASSWD: /home/rocroshan/Desktop/SIH(RF)/tyech-erase

Notes and security guidance
- Only allow the exact wrapper path. Do not use wildcards or allow sudo for broad commands.
- Ensure the wrapper (`tyech-erase`) is owned and writable only by a trusted admin (chmod 750/700) so it cannot be modified by unprivileged users.
- Consider creating a small privileged helper that performs only the minimal privileged steps, and keep that helper audited.
- Test the rule by switching to the web user and running the wrapper (e.g., `sudo -u www-data /home/rocroshan/Desktop/SIH(RF)/tyech-erase --list`).

If you want, I can generate a safe `systemd` service or a small privileged helper that performs erases via a controlled IPC channel (safer than granting wide sudo rights). Tell me which approach you prefer.
