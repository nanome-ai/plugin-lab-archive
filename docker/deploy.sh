if [ "$(docker ps -aq -f name=nanome-lab-archives)" != "" ]; then
    # cleanup
    echo "removing exited container"
    docker rm -f nanome-lab-archives
fi

HOST=`ipconfig getifaddr en0`

docker run -d \
--name nanome-lab-archives \
--restart unless-stopped \
-e ARGS="$*" \
-e HOSTNAME=$HOST \
-v postnome-volume:/root \
nanome-lab-archives
