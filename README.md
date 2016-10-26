This repository contains a Python 3 script for automatically configuring the
current CentOS kernel on [DigitalOcean][do] CentOS droplets and restarting.

The script uses the DigitalOcean API and ssh to apply those steps
to all droplets where the running kernel is outdated.

**Update (2016-10):** Since June, 2016, the script is more of
historic interest (and an example how to use the DigitalOcean v2
API) because DigitalOcean started to provide a GrubLoader for
CentOS (cf. the Background Section).

2016, Georg Sauthoff <mail@georg.so>

## History

DigitalOcean CentOS images [were a little bit special
with respect to kernel upgrades][1]. A `yum update && shutdown -r now`
wasn't enough to get the latest stable kernel with all the security fixes.
Instead one had to explicitly select the right kernel version outside of
the VM (e.g. via the frontend or API) and reboot the doplet.

## Background

DigitalOcean silently stopped providing any CentOS
kernel updates for their control panel since August, 2016 or so.

Also without any announcement, the DigitalOcean control panel now
provides GrubLoader 'kernels' for CentOS ([since June, 2016 or so][3]):

    DigitalOcean GrubLoader v0.1 (20160527) CentOS
    DigitalOcean GrubLoader v0.2 (20160714) CentOS

With that, updating the kernel on a CentOS droplet is as easy as
everywhere else, i.e. it is just a `yum update` and `shutdown -r
now` away. Apparently, this [took them 3 years or so][2] (the
2013 date on the article is misleading, it wasn't updated when
the new CentOS content was added).

That means that the new recommended way to setup a CentOS droplet
is to just configure the GrubLoader 'kernel' and do standard
kernel updating.

Note that when switching an existing droplet to GrubLoader, one
still has to execute the old procedure once: select the
GrubLoader in the control panel (or via the API), power off the
system and power it on again (via the control panel/API).

[do]: https://en.wikipedia.org/wiki/DigitalOcean
[1]: https://www.digitalocean.com/community/questions/kernel-update
[2]: https://www.digitalocean.com/community/tutorials/how-to-update-a-digitalocean-server-s-kernel
[3]: https://www.reddit.com/r/linux/comments/4whi9i/fyi_digital_ocean_now_lets_you_run_your_own/?st=irlrmj8c&sh=76cd1e99
