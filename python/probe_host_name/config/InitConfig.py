#!/usr/bin/env python2.7
# -*- coding: utf-8

import os
import sys
import configparser


class InitConfig:
    config_dir = os.path.dirname(os.path.realpath(__file__))
    config_file = ""

    def __init__(self):
        pass

    @staticmethod
    def get_config(file_name=None):
        config = configparser.ConfigParser()
        params = {}        
        if file_name is not None:
            if not file_name.endswith(".ini"):
                file_name += ".ini"
            # self.config_file = os.path.join(self.config_dir, file_name)
            InitConfig.config_file = os.path.join(InitConfig.config_dir, file_name)        
        if os.path.exists(InitConfig.config_file):
            config.read(InitConfig.config_file)
            for section in config.sections():
                for keys in config[section]:
                    params[keys] = config[section][keys]
        else:
            raise Exception("Error : File configuration not found !! -> %s" % InitConfig.config_file)            
        return params
    
    @staticmethod
    def get_config_by_section(file_name=None):        
        config = configparser.ConfigParser()
        params = {}
        section_params = {}
        list_params = []
        if file_name is not None:
            if not file_name.endswith(".ini"):
                file_name += ".ini"        
            InitConfig.config_file = os.path.join(InitConfig.config_dir, file_name)        
        if os.path.exists(InitConfig.config_file):
            config.read(InitConfig.config_file)
            for section in config.sections():
                for keys in config[section]:
                    params[keys] = config[section][keys]                    
                section_params[section] = params                
                list_params.append(section_params)
                params = {} # reset
                section_params = {} # reset
        else:
            raise Exception("Error : File configuration not found !! -> %s" % InitConfig.config_file)            
        return list_params

    @staticmethod
    def get_config_by_section2(file_name=None):        
        config = configparser.ConfigParser()
        params = {}
        section_params = {}
        list_params = []
        if file_name is not None:
            if not file_name.endswith(".ini"):
                file_name += ".ini"        
            InitConfig.config_file = os.path.join(InitConfig.config_dir, file_name)        
        if os.path.exists(InitConfig.config_file):
            config.read(InitConfig.config_file)
            for section in config.sections():
                for keys in config[section]:
                    params[keys] = config[section][keys]       
                section_params['category_title'] = section
                section_params['category_param'] = params               
                list_params.append(section_params)
                params = {} # reset
                section_params = {} # reset
        else:
            raise Exception("Error : File configuration not found !! -> %s" % InitConfig.config_file)            
        return list_params
    
    @staticmethod
    def get_config_by_section_name(file_name=None, section=None):
        if section is not None:  
            configuration = InitConfig.get_config_by_section2(file_name=file_name)  
            config = list(filter(lambda x: x.get('category_title').lower() == section.lower(), configuration))
            if len(config) == 0:
                print "Error: Section '%s' is not found on '%s'" % (section, InitConfig.config_file)
                sys.exit(-1)
            return config[0].get('category_param')
        else:
            # print "Error : Section not Found:  %s on %s" % (section, InitConfig.config_file)
            raise Exception("Error : You need to defined Section on:  %s" % InitConfig.config_file)            
        return list_params
    