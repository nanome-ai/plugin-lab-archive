if [[ $(docker volume ls -f name=la-volume -q) ]]; then
    echo "Skipping volume creation"
else
    echo "Creating new docker volume"
    docker volume create la-volume
fi

docker build -f Dockerfile -t nanome-lab-archives:latest ..