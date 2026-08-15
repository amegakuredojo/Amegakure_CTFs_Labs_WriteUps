const cp = require("child_process");
const cmds = [
  "id",
  "groups",
  "for d in /usr/local/sbin /usr/local/bin /usr/sbin /usr/bin /sbin /bin /snap/bin; do [ -w \"$d\" ] && echo WRITABLE_PATH:$d; done",
  "[ -w / ] && echo ROOT_FS_WRITABLE || echo ROOT_FS_NOT_WRITABLE",
  "find / -perm -4000 -type f 2>/dev/null | grep -vE '^/usr/(bin|sbin|lib)'",
  "id | tr ' ' '\\n' | grep -iE 'lxd|docker|sudo|root|adm' || echo NO_PRIV_GROUPS",
  "ls -la /home",
  "find /etc/cron* -writable 2>/dev/null; echo CRON_DONE",
  "ls -la /var/spool/cron 2>/dev/null; ls -la /var/spool/cron/crontabs 2>/dev/null"
];
for (const c of cmds) {
  try {
    const o = cp.execSync("bash -lc " + JSON.stringify(c + " 2>&1 || true")).toString();
    console.log("### " + c + "\n" + o);
  } catch (e) {
    console.log("ERR " + c + " " + e.message);
  }
}
