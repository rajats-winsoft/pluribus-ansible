#!/usr/bin/python
# Test PN CLI vlag-create/vlag-delete
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
#

import subprocess
import shlex

DOCUMENTATION = """
---
module: pn_vlag
author: "Pluribus Networks"
short_description: CLI command to create/delete vlag.
description:
  - Execute vlag-create or vlag-delete command.
  - Requires vlagname:
    - Alphanumeric characters
    - Special characters like: _
options:
  pn_cliusername:
    description:
      - Login username
    required: true
    type: str
  pn_clipassword:
    description:
      - Login password
    required: true
    type: str
  pn_vlagcommand:
    description:
      - The C(pn_vlagcommand) takes the vlag-create/delete command as value.
    required: true
    choices: vlag-create, vlag-delete
    type: str
  pn_vlagname:
    description:
      - The C(pn_vlagname) takes a valid name for vlag configuration.
    required: true
    type: str
  pn_vlaglport:
    description:
      - the local VLAG port.
    required_if: vlag-create
    type: str
  pn_vlagpeerport:
    description:
      - the VLAG peer-port.
    required_if: vlag-create
    type: str
  pn_vlagmode:
    description:
      - the VLAG mode.
    required: False
    choices: active-active, active-standby
    type: str
  pn_vlagpeerswitch:
    description:
      - the VLAG peer switch.
    required: False
    type: str
  pn_vlagfailover:
    description:
      - failover-move-L2 sends gratuitous APRs or not.
    required: False
    choices: failover-move-L2, failover-ignore-L2
    type: str
  pn_vlaglacpmode:
    description:
      - the LACP mode
    required: False
    choices: off, passive, active
    type: str
  pn_vlaglacptimeout:
    description:
      - the LACP timeout
    required: False
    choices: slow, fast
  pn_vlagfallback:
    description:
      - the LACP fallback mode
    required: False
    choices: individual, bundled
    type: str
  pn_vlagfallbacktimeout:
    description:
      - LACP fallback timeout
    required: False
    coices: 30...60 seconds. Defaut is 50 seconds.
    type: str
  pn_quiet:
    description:
      - The C(pn_quiet) option to enable or disable the system bootup message.
    required: false
    type: bool
    default: true
"""

EXAMPLES = """
- name: create a VLAG
  pn_vlag:
    pn_cliusername: admin
    pn_clipassword: admin
    pn_vlagcommand: 'vlag-create'
    pn_vlagname: 'vlag-1'
    pn_vlaglport: 'spine01'
    pn_vlagpeerport: 'spine02'
    pn_vlagmode: 'active-active'
    pn_quiet: True

- name: delete VLAGs
  pn_vlag:
    pn_cliusername: admin
    pn_clipassword: admin
    pn_vlagcommand: 'vlag-delete'
    pn_vlagname: vlag-1
    pn_quiet: True
"""

RETURN = """
vlagcmd:
  description: the CLI command run on the target node(s).
stdout:
  description: the set of responses from the vlag command.
  returned: always
  type: list
stdout_lines:
  description: the value of stdout split into a list.
  returned: always
  type: list
stderr:
  description: the set of error responses from the vlag command.
  returned: on error
  type: list
changed:
  description: Indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
"""


def main():
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=True, type='str'),
            pn_clipassword=dict(required=True, type='str'),
            pn_vlagcommand=dict(required=True, type='str',
                                choices=['vlag-create', 'vlag-delete']),
            pn_vlagname=dict(required=True, type='str'),
            pn_vlaglport=dict(type='str'),
            pn_vlagpeerport=dict(type='str'),
            pn_vlagmode=dict(required=False, type='str',
                             choices=['active-standby', 'active-active']),
            pn_vlagpeerswitch=dict(required=False, type='str'),
            pn_vlagfailover=dict(required=False, type='str',
                                 choices=['failover-move-L2',
                                          'failover-ignore-L2']),
            pn_vlaglacpmode=dict(required=False, type='str',
                                 choices=['off', 'passive', 'active']),
            pn_vlaglacptimeout=dict(required=False, type='str',
                                    choices=['slow', 'fast']),
            pn_vlagfallback=dict(required=False, type='str',
                                 choices=['individual', 'bundled']),
            pn_vlagfallbacktimeout=dict(required=False, type='str'),
            pn_quiet=dict(default=True, type='bool')
        ),
        required_if=(
            ["pn_vlagcommand", "vlag-create",
             ["pn_vlagname", "pn_vlaglport", "pn_vlagpeerport"]],
            ["pn_vlagcommand", "vlag-delete", ["pn_vlagname"]]
        )
    )

    cliusername = module.params['pn_cliusername']
    clipassword = module.params['pn_clipassword']
    vlagcommand = module.params['pn_vlagcommand']
    vlagname = module.params['pn_vlagname']
    vlaglport = module.params['pn_vlaglport']
    vlagpeerport = module.params['pn_vlagpeerport']
    vlagmode = module.params['pn_vlagmode']
    vlagpeerswitch = module.params['pn_vlagpeerswitch']
    vlagfailover = module.params['pn_vlagfailover']
    vlaglacpmode = module.params['pn_vlaglacpmode']
    vlaglacptimeout = module.params['pn_vlaglacptimeout']
    vlagfallback = module.params['pn_vlagfallback']
    vlagfallbacktimeout = module.params['pn_vlagfallbacktimeout']
    quiet = module.params['pn_quiet']

    if quiet is True:
        cli = ('/usr/bin/cli --quiet --user ' + cliusername + ':' +
               clipassword + ' ')
    else:
        cli = '/usr/bin/cli --user ' + cliusername + ':' + clipassword + ' '

    vlag = cli
    if vlagname:
        vlag += vlagcommand + ' name ' + vlagname

    if vlaglport:
        vlag += ' port ' + str(vlaglport)

    if vlagpeerport:
        vlag += ' peer-port ' + str(vlagpeerport)

    if vlagmode:
        vlag += ' mode ' + vlagmode

    if vlagpeerswitch:
        vlag += ' peer-switch' + vlagpeerswitch

    if vlagfailover:
        vlag += ' ' + vlagfailover

    if vlaglacpmode:
        vlag += ' lacp-mode ' + vlaglacpmode

    if vlaglacptimeout:
        vlag += ' lacp-timeout' + vlaglacptimeout

    if vlagfallback:
        vlag += ' lacp-fallback ' + vlagfallback

    if vlagfallbacktimeout:
        vlag += ' lacp-fallback-timeout ' + vlagfallbacktimeout

    vlagcmd = shlex.split(vlag)
    response = subprocess.Popen(vlagcmd, stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE, universal_newlines=True)
    out, err = response.communicate()

    if out:
        module.exit_json(
            vlagcmd=vlag,
            stdout=out.rstrip("\r\n"),
            changed=True
        )
    if err:
        module.exit_json(
            vlagcmd=vlag,
            stderr=err.rstrip("\r\n"),
            changed=False
        )

from ansible.module_utils.basic import AnsibleModule

if __name__ == '__main__':
    main()
