#!/usr/bin/env python3

# Configure the current CentOS kernel on all droplets
# and restart where necessary.
#
# Background: Digital Ocean CentOS images are a little bit special
# with respect to kernel upgrades. A `yum update && shutdown -r now`
# is not enough to get the latest stable kernel with all the security fixes.
# Instead one has to explicitly select the right kernel version outside of
# the VM (e.g. via the frontend or API) and reboot the doplet.
#
# The script uses the digital ocean API and ssh to apply those steps
# to all droplets where the running kernel is outdated.
#
# 2016, Georg Sauthoff <mail@georg.so>, GPL3+

import os
import requests
import subprocess
import pprint

bearer = os.getenv('bearer')

def mk_headers(bearer):
  return { 'Content-Type': 'application/json', 'Authorization': 'Bearer {}'.format(bearer) }

def droplets(bearer):
  r = requests.get('https://api.digitalocean.com/v2/droplets?page=1&per_page=100', headers = mk_headers(bearer))
  if r.status_code != 200:
    raise Exception(r.text)
  return r.json()['droplets']

def available_kernels(bearer, droplet_id):
  r = requests.get('https://api.digitalocean.com/v2/droplets/{}/kernels?page=1&per_page=1000'.format(droplet_id),
      headers = mk_headers(bearer))
  if r.status_code != 200:
    raise Exception(r.text)
  return r.json()['kernels']

def latest_kernel(kernels):
  fs = [ k for k in kernels if k['name'].startswith('CentOS 7') ]
  ss = sorted(fs, key=lambda x: [ int(a) for a in x['version'].replace('-', '.').split('.') if a.isdigit() ] )
  latest = ss[-1]
  print('Latest available kernel is: {}'.format(latest['name']))
  return latest

def change_kernel(bearer, droplet_id, kernel_id):
  print('Setting new kernel id: {}'.format(kernel_id))
  r = requests.post('https://api.digitalocean.com/v2/droplets/{}/actions'.format(droplet_id),
      headers = mk_headers(bearer),
      json = { 'type': 'change_kernel', 'kernel': kernel_id } )
  print('Status code: {}'.format(r.status_code))
  if r.status_code not in [200, 201]:
    raise Exception(r.text)
  return r.json()['action']

def verify_action_completed_prime(bearer, action_id):
  print('Verifying action completed, id: {}'.format(action_id))
  for i in range(10):
    r = requests.get('https://api.digitalocean.com/v2/actions/{}'.format(action_id),
        headers = mk_headers(bearer))
    if r.status_code == 200:
      a = r.json()['action']
      if a['id'] == action_id and a['status'] == 'completed':
        return
    if r.status_code != 201:
      raise Exception(r.text)
    time.sleep(3)
  raise Exception('Action {} still not completed'.format(action_id))

def verify_action_completed(bearer, action, desc):
  if action['status'] == 'in-progress':
    verify_action_completed_prime(bearer, action['id'])
  elif action['status'] == 'completed':
    pass
  else:
    raise Exception('{} returned error status: {}'.format(desc, action['status']))

def shutdown(hostname):
  try:
    print('Shutting down {}'.format(hostname))
    subprocess.check_output(['ssh', hostname, 'shutdown', '-h', 'now'], stderr=subprocess.STDOUT)
  except subprocess.CalledProcessError as e:
    if e.returncode != 255:
      raise

def verify_status(bearer, droplet_id, value):
  print('Verifying status {} on droplet id: {}'.format(value, droplet_id))
  for i in range(10):
    r = requests.get('https://api.digitalocean.com/v2/droplets/{}'.format(droplet_id),
        headers = mk_headers(bearer))
    if r.status_code == 200:
      d = r.json()['droplet']
      if d['status'] == value:
        return
    else:
      raise Exception(r.text)
    time.sleep(3)
  raise Exception('Droplet {} still not {}'.format(droplet_id, value))

def power_on(bearer, droplet_id):
  print('Power on droplet id: {}'.format(droplet_id))
  r = requests.post('https://api.digitalocean.com/v2/droplets/{}/actions'.format(droplet_id),
      headers = mk_headers(bearer),
      json = { 'type': 'power_on' } )
  print('Status code: {}'.format(r.status_code))
  if r.status_code not in [200, 201]:
    raise Exception(r.text)
  return r.json()['action']

def verify_running_kernel(expected_version, hostname):
  actual_version = subprocess.check_output(['ssh', hostname, 'uname', '-r']).decode('ascii').strip()
  if expected_version != actual_version:
    raise Exception('Host {} is running kernel {} although we just rebooted to {}'.format(
      hostname, actual_version, expected_version))

# cf. ~/info/digitalocean

def main(bearer):
  ds = droplets(bearer)
  for droplet in ds:
    droplet_id = droplet['id']
    name = droplet['name']
    print('Checking droplet: id={}'.format(droplet_id))
    kernels = available_kernels(bearer, droplet_id)
    latest = latest_kernel(kernels)
    if droplet['kernel']['id'] != latest['id']:
    #if True:
      print('Droplet has kernel {}, thus upgrading to the latest, i.e. {}'
          .format(droplet['kernel']['name'], latest['name']))
      action = change_kernel(bearer, droplet_id, latest['id'])
      verify_action_completed(bearer, action, 'Changing kernel')
      shutdown(name)
      verify_status(bearer, droplet_id, 'off')
      action = power_on(bearer, droplet_id)
      verify_action_completed(bearer, action, 'Powering on')
      verify_status(bearer, droplet_id, 'active')
      verify_running_kernel(latest['version'], name)

# XXX use logging instead of print()

if __name__ == '__main__':
  main(bearer)

