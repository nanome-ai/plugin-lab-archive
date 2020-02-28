if [[ $(docker volume ls -f name=la-volume -q) ]]; then
    echo "Skipping volume creation"
else
    echo "Creating new docker volume"
    docker volume create la-volume
fi

cp ../../credentials/lab-archives/credentials.txt ..
docker build -f Dockerfile -t nanome-lab-archives:latest ..
rm ../credentials.txt