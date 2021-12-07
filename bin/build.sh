#!/usr/bin/env sh

script_path=$(readlink -f "$0")
bin_path=$(dirname "$script_path")
app_path=$(dirname "$bin_path")
app_version=0.2.4
docker_path=$app_path/docker
docker_repo_config_path=$docker_path/repo.cfg
docker_repo=
docker_distro=alpine
docker_distro_tag=3.14
docker_tag=$app_version-$docker_distro-$docker_distro_tag-mysql

if [ ! -z "$1" ];
then
    docker_tag=$1
fi

if [ ! -z "$2" ];
then
    app_version=$2
fi

if [ ! -z "$3" ];
then
    docker_distro=$3
fi

if [ ! -z "$4" ];
then
    docker_distro_tag=$4
fi

if [ -f "$docker_repo_config_path" ];
then
    docker_repo=`cat $docker_repo_config_path`

    if [ -f "$docker_path/$docker_distro/Dockerfile-$docker_tag" ];
    then
        docker_file=$docker_path/$docker_distro/Dockerfile-$docker_tag
    elif [ -f "$docker_path/$docker_distro/Dockerfile-$docker_distro-$docker_distro_tag" ];
    then
        docker_file=$docker_path/$docker_distro/Dockerfile-$docker_distro-$docker_distro_tag
    elif [ -f "$docker_path/$docker_distro/Dockerfile-$docker_distro" ];
    then
        docker_file=$docker_path/$docker_distro/Dockerfile-$docker_distro
    else
        docker_file=$docker_path/$docker_distro/Dockerfile
    fi

    docker build --force-rm -f $docker_file -t $docker_repo:$docker_tag --build-arg DISTRO=$docker_distro --build-arg DISTRO_TAG=$docker_distro_tag $app_path

else
    echo "Could not load Docker registry path from $docker_repo_config_path"
    exit 1
fi

exit