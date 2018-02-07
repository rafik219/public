#!/bin/env python3.5
# -*- coding: utf-8 -*-

# # # # # # # # # # # # # # # # # # # # #
# author: rbo
# version: 07/02/2018
#
# utility: - Getting Jenkins jobs status
#          - Get information for job
# require:
# - python3
# - not tested on python2
#
# # # # # # # # # # # # # # # # # # # # #

import argparse
import os
import sys
from json import loads
from urllib.error import URLError, HTTPError
from urllib.request import urlopen

import yaml


def usage():
    usage = """ 
    usage: JenkinsList.py [-h] -c CONFIG_FILE {list,info} ...

    This is the description                                  

    positional arguments:                                    
      {list,info}     command                                
        list          List all jobs                          
        info          get info from job name                 

    optional arguments:                                      
      -h, --help      show this help message and exit        
      -c CONFIG_FILE  Yaml configuration file                     
    """
    print(usage)
    sys.exit(0)


class JenkinsApi:
    def __init__(self, url, port, auth=None, username=None, token=None):
        self.jenkins_url = url
        self.jenkins_port = port
        if auth is not None:
            self._jenkins_username = username
            self._jenkins_token = token
        self.json_response = self.get_json_response()

    def get_json_response(self, url=None, username=None, token=None):
        """
        :param url:         URL of jenkins
        :param username:    Used to access to jenkins (None by default)
        :param token:       Used to authenticate to jenkins (None by default)
        :return:            Dictionary containing  all information for jobs
        """
        json_response = {}
        if url is None:
            json_url = "{0}:{1}/api/json".format(self.jenkins_url, self.jenkins_port)
        else:
            json_url = url
        try:
            url_data = urlopen(json_url)
            encoding = url_data.info().get_content_charset('utf-8')
            json_response = loads(url_data.read().decode(encoding))
        except HTTPError as ex:
            print("Server couldn't fulfill the request, cause: {}".format(ex))
            print("Error code: {}".format(ex.code))
        except URLError as ex:
            print("Failed to reach a server, cause: {}".format(ex.reason))
        except Exception as ex:
            print("Failed to load JSON response from Jenkins API, cause: {}".format(ex))
        return json_response

    def display_list_jobs(self):
        """
        Display list of all jobs found on jenkins with different status
        (Name,    Status,      Url)
        :return:
        """
        if len(self.json_response) != 0:
            print("\n- Listing jobs on Node: '{}'\n".format(self.json_response.get('nodeName')))
            print("{:60} {:15} {:60}".format("NAME", "STATUS", "URL"))
            print("{:-^60} {:-^15} {:-^60}".format("", "", ""))
            # filter jobs with color status
            jobs = filter(lambda k: k.get('color') is not None, self.json_response.get('jobs'))
            # order jobs by color
            for job in sorted(jobs, key=lambda k: k['color']):
                job_name = job.get('name').upper()
                job_color = job.get('color').upper()
                job_url = job.get('url')
                print("{:60} {:15} {:60}".format(job_name, job_color, job_url))

    def display_job_information(self, job_name):
        """
        Find and display information about job.
            -   Name
            -   URL
            -   Number of build
            -   Last  build
        :param job_name:  job name
        :return:
        """
        found = False
        if len(self.json_response) != 0:
            if self.json_response.get('nodeName') is not None:
                node_name = self.json_response.get('nodeName')
                print(node_name)
            for job in sorted(self.json_response.get('jobs'), key=lambda k: k['name']):
                if job_name == job.get('name'):
                    # print("Found !! : %s" % job_name)
                    found = True
                    break
            if found:
                job_info_url = "{0}:{1}/job/{2}/api/json".format(self.jenkins_url, self.jenkins_port, job_name)
                job_info = self.get_json_response(job_info_url)
                print("- This is information found for '{}' job:\n".format(job_name))
                print("JOB NAME          : {}".format(job_info.get('name')))
                print("JOB URL           : {}".format(job_info.get('url')))
                print("JOB NUMBER BUILD  : {}".format(len(job_info.get('builds'))))
                print("JOB LAST BUILD    : {}".format(job_info.get('color')))
                # print("JOB DESCRIPTION   : {}".format(job_info.get('description')))
            else:
                print("Job Name : '{}' Not Found !!".format(job_name))

    @staticmethod
    def get_configuration(yaml_file):
        """
        Static method used to read and get configuration from config.yaml file
        :param yaml_file: YAML file configuration
        :return: dictionary of all information
        """
        if os.path.exists(yaml_file):
            with open(yaml_file, 'r') as f:
                try:
                    config = yaml.load(f)
                    return config
                except Exception as ex:
                    print("ERROR: during loading configuration file : {0}, cause: {1}".format(yaml_file, ex))
                    sys.exit(-1)
        else:
            print("ERROR: configuration file {} not found !!".format(yaml_file))
            sys.exit(-2)


def main():
    parser = argparse.ArgumentParser(description="This is the description")
    parser.add_argument("-c", action="store", dest="config_file", type=argparse.FileType('r'), nargs=1,
                        help="Yaml configuration file", required=True)

    sub_parser = parser.add_subparsers(help="command", dest="command")
    sub_parser.add_parser('list', help="List all jobs")

    info_parser = sub_parser.add_parser('info', help="get info from job name")
    info_parser.add_argument('job_name', help="Job Name", nargs=1, action="store")

    args = parser.parse_args()

    if args.command is None:
        parser.error("choose from ['list', 'info']")

    # Get configuration
    config = JenkinsApi.get_configuration(args.config_file[0].name)

    if args.command == "list":
        for server in config.get('servers'):
            jenkins = JenkinsApi(server.get('url'), server.get('port'))
            jenkins.display_list_jobs()
    if args.command == "info":
        for server in config.get('servers'):
            jenkins = JenkinsApi(server.get("url"), server.get('port'))
            jenkins.display_job_information(args.job_name[0])


if __name__ == '__main__':
    main()
    print("SUCCESS !!")
