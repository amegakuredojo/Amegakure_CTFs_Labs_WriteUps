set +e
echo LBL_12bn_hex; od -An -tx1 /bin/12bn 2>&1
echo LBL_akpk1_hex; od -An -tx1 /opt/ak.pk1 2>&1
echo LBL_cal_home; sudo -u calamardo /bin/node -e 'const fs=require("fs");try{console.log(fs.readdirSync("/home/calamardo"))}catch(e){console.log("err:"+e.message)}'
echo LBL_pat_home_node; sudo -u calamardo /bin/node -e 'const fs=require("fs");try{console.log(fs.readdirSync("/home/patricio"))}catch(e){console.log("err:"+e.message)}'
echo LBL_read_cal_profile; sudo -u calamardo /bin/node -e 'const fs=require("fs");try{console.log(fs.readFileSync("/home/calamardo/.profile","utf8"))}catch(e){console.log("err:"+e.message)}'
echo LBL_find_suid_all; find / -perm -4000 -type f 2>/dev/null
echo LBL_etc_passwd_tail; tail -5 /etc/passwd
echo LBL_services; ls /etc/systemd/system 2>/dev/null; ls /etc/init.d 2>/dev/null
