set +e
echo LBL_id; id
echo LBL_sudoln; sudo -n -l 2>&1
echo LBL_customsuid; find / -perm -4000 -type f 2>/dev/null | grep -vE '^/usr/(bin|sbin|lib)'
echo LBL_caps; /sbin/getcap -r / 2>/dev/null
echo LBL_writepath; for d in $(echo $PATH|tr : ' '); do [ -w "$d" ] && echo WR:$d; done
echo LBL_homecal; ls -la /home/calamardo 2>&1
echo LBL_homepat; ls -la /home/patricio 2>&1
echo LBL_opt; ls -la /opt 2>&1; echo OPT_AK:; cat /opt/ak.pk1 2>&1; echo; echo BIN12:; cat /bin/12bn 2>&1
echo LBL_ps; ps aux 2>/dev/null | head -15
echo LBL_sudoersd; ls -la /etc/sudoers.d/ 2>&1
echo LBL_usrlocalbin; ls -la /usr/local/bin 2>&1
echo LBL_profile; head -c 200 /home/bob/.profile | xxd | head -8
