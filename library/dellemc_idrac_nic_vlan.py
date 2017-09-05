#! /usr/bin/python
# _*_ coding: utf-8 _*_

#
# Copyright (c) 2017 Dell Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: dellemc_idrac_nic_vlan
short_description: Configure iDRAC Network VLAN settings
version_added: "2.3"
description: Configure following iDRAC Network VLAN settings:
    - Enable VLAN : Enable/disable VLAN
    - VLAN ID (must be a value from 1 to 4094)
    - VLAN Priority (must be a value from 0 to 7)
options:
    idrac_ip:
        required: False
        description: iDRAC IP Address
        default: None
    idrac_user:
        required: False
        description: iDRAC user name
        default: None
    idrac_pwd:
        required: False
        description: iDRAC user password
        default: None
    idrac_port:
        required: False
        description: iDRAC port
        default: None
    share_name:
        required: True
        description: CIFS or NFS Network share 
    share_user:
        required: True
        description: Network share user in the format user@domain
    share_pwd:
        required: True
        description: Network share user password
    share_mnt:
        required: True
        description: Local mount path of the network file share with
        read-write permission for ansible user
    vlan_id:
        required: False
        description: VLAN ID
        default: 1
    vlan_priority:
        required: False
        description: VLAN priority
        default: 0
    state:
        required: False
        description:
        - if C(enable), will enable the VLAN settings and add/change VLAN ID and
          VLAN priority
        - if C(disable), will disable the VLAN settings
        default: 'disable'

requirements: ['omsdk']
author: "anupam.aloke@dell.com"
"""

from ansible.module_utils.basic import AnsibleModule

try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError

# Setup iDRAC Network File Share
# idrac: iDRAC handle
# module: Ansible module
#
def _setup_idrac_nw_share (idrac, module):
    from omsdk.sdkfile import FileOnShare
    from omsdk.sdkcreds import UserCredentials

    myshare = FileOnShare(module.params['share_name'],
                          module.params['share_mnt'],
                          isFolder=True)

    myshare.addcreds(UserCredentials(module.params['share_user'],
                                    module.params['share_pwd']))

    return idrac.config_mgr.set_liason_share(myshare)

# setup_idrac_nic_vlan
# idrac: iDRAC handle
# module: Ansible module
#
def setup_idrac_nic_vlan (idrac, module):

    msg = {}
    msg['changed'] = False
    msg['failed'] = False
    err = False

    try:
        # Check first whether local mount point for network share is setup
        if idrac.config_mgr.liason_share is None:
            if not  _setup_idrac_nw_share (idrac, module):
                msg['msg'] = "Failed to setup local mount point for network share"
                msg['failed'] = True
                return msg, err

        # TODO: Check whether VLAN settings exists or not
        enabled = False

        if module.params["state"] == "enable":
            if module.check_mode or enabled: 
                msg['changed'] = not enabled 
            else:
                msg['msg'] = idrac.config_mgr.enable_idracnic_vlan(
                                             module.params["vlan_id"],
                                             module.params["vlan_priority"])

                if msg['msg']["Status"] is not "Success":
                    msg['failed'] = True
                else:
                    msg['changed'] = True

        else:
            if module.check_mode or not enabled:
                msg['changed'] = enabled
            else:
                msg['msg'] = idrac.config_mgr.disable_idracnic_vlan()

                if msg['msg']["Status"] is not "Success":
                    msg['failed'] = True
                else:
                    msg['changed'] = True

    except Exception as e:
        err = True
        msg['msg'] = "Error: %s" % str(e)
        msg['failed'] = True

    return msg, err


# Main
def main():
    from ansible.module_utils.dellemc_idrac import iDRACConnection

    module = AnsibleModule (
            argument_spec = dict (

                # iDRAC handle
                idrac = dict (required = False, type = 'dict'),

                # iDRAC Credentials
                idrac_ip   = dict (required = True, type = 'str'),
                idrac_user = dict (required = False, default = None, type = 'str'),
                idrac_pwd  = dict (required = False, default = None,
                                   type = 'str', no_log = True),
                idrac_port = dict (required = False, default = None),

                # Network File Share
                share_name = dict (required = True, default = None),
                share_user = dict (required = True, default = None),
                share_pwd  = dict (required = True, default = None),
                share_mnt  = dict (required = True, default = None),

                # iDRAC Network VLAN Settings
                vlan_id = dict (required = False, default = 1, type = 'int'),
                vlan_priority = dict (required = False, default = 0, type = 'int'),
                state = dict (required = False, choices = ['enable', 'disable'],
                              default = 'enable')
                ),
            supports_check_mode = True)

    # Connect to iDRAC
    idrac_conn = iDRACConnection (module)
    idrac = idrac_conn.connect()

    (msg, err) = setup_idrac_nic_vlan (idrac, module)

    # Disconnect from iDRAC
    idrac_conn.disconnect()

    if err:
        module.fail_json(**msg)
    module.exit_json(**msg)


if __name__ == '__main__':
    main()
