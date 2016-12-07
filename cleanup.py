#! /usr/bin/env python3
#
# Copyright 2016 leftcoast.io, inc
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
#
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse

import docker
from docker.errors import APIError


def extract_id(image):
    return image['Id'].split(":")[1]


def cleanup(verbose, nucler):
    client = docker.from_env(assert_hostname=False)
    client.timeout = 20

    if verbose:
        print("\tdocker client version {}".format(client.version()))
        print("\tlooking for exited containers to remove")

    data_image_id = 0

    for c in client.containers(size=True, trunc=False, all=nucler,
                               filters={'status': 'exited'}):
        name = (c['Names'][0]).replace("/", "")
        if verbose:
            print("\tremoving exited container {}".format(name))

        client.remove_container(container=name)

    if verbose:
        print("\t{} active containers remain".format(
                len(client.containers(all=True))))
        print("\tlooking for dangling images to remove")

    if nucler:
        for i in client.images(all=True):
            image_id = extract_id(i)
            if image_id != data_image_id:
                if verbose:
                    print("\tremoving any image {}".format(image_id))
    else:
        for i in client.images(filters={'dangling': True}):
            image_id = extract_id(i)
            if image_id != data_image_id:
                if verbose:
                    print("\tremoving dangling image {}".format(image_id))

            try:
                client.remove_image(image=image_id)
            except APIError:
                if verbose:
                    print("\tignoring  in use  image {}".format(image_id))

    if verbose:
        print("\t{} non-dangling images remain".format(
                len(client.images(all=True))))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
            prog='cleanup.py',
            usage='cleanup.py [--all]',
            description='Remove exited containers')

    parser.add_argument(
            '--verbose',
            dest='verbose',
            action='store_true',
            default=False,
            help='display the name of the container before deleting it')

    args = parser.parse_args()

    cleanup(args.verbose, False)
