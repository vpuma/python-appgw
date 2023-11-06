CREATE DATABASE IF NOT EXISTS appgw DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;

use appgw;

CREATE TABLE IF NOT EXISTS `task` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '设置主键自增',
  `name` varchar(500) NOT NULL COMMENT 'task name, i.e. nlt01.vtc365.com_4025_99395',
  `provider_id` int(11) NOT NULL COMMENT  'provider id in table provider',
  `create_time` datetime NOT NULL COMMENT  'time of creating, i.e. 20230618 15:00:20',
  `status` varchar(50) NOT NULL COMMENT  'task status, i.e. CREATING, IP, STOP',
  `video_url` varchar(500) NOT NULL COMMENT 'video url, i.e. http://test.vtc365.com/s22/1234/live.m3u8',  
  `update_timestamp` timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'timestamp of the last update',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `provider` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '设置主键自增',
  `type` varchar(100) NOT NULL COMMENT 'service type, i.e. aiapp',
  `version` varchar(100) NOT NULL COMMENT 'service version, i.e. 1.0.2',
  `host` varchar(100) NOT NULL COMMENT 'host, i.e. 192.168.0.12',
  `port` int(11) NOT NULL COMMENT 'port, i.e. 8010', 
  `path` varchar(100) NOT NULL  COMMENT 'path, i.e. /aipp', 
  `ttl` int(11) NOT NULL COMMENT 'TTL, a countdown value, >0 active <=0 inactive', 
  `active` tinyint(1) NOT NULL COMMENT '1-active  0-inactive', 
  `cpuload` float NOT NULL COMMENT 'cpu load, i.e. 25.03', 
  `update_timestamp` timestamp DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'timestamp of the last update',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

CREATE TABLE IF NOT EXISTS `service` (
  `id` int(11) NOT NULL AUTO_INCREMENT COMMENT '设置主键自增',
  `type` varchar(100) NOT NULL COMMENT 'service type, i.e. aiapp',
  `valid` tinyint(1) NOT NULL COMMENT '1-valid  0-invalid',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

