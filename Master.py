#!/usr/bin/python3
# Author: Zhuangwei Kang
# -*- coding: utf-8 -*-

import HAProxyAPI as lb
import K8sAPI as k8s


class Master:
    def __init__(self):
        self.k8sclient = k8s.K8sAPI()