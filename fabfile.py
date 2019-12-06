# -*- coding: utf-8 -*-

from datetime import datetime
from fabric.api import *
from fabvenv import virtualenv

# 登录用户和主机名：
env.user = 'ubuntu'
env.password = 'Cmx170904'
env.hosts = ['106.54.217.74']
pack_name = 'deploypack_hydrology_mgmt.tar.gz'


def pack():
    ' 定义一个pack任务 '
    # 打一个tar包：
    local('del %s' % pack_name)
    local('md ..\pack_tmp')
    local('xcopy /e /s .\* ..\pack_tmp')
    with lcd('..\pack_tmp'):
        local('tar -czvf ../hydrology_mgmt/%s --exclude *.pyc --exclude fabfile.py '
              '--exclude 00* --exclude *.tar.gz --exclude README.md --exclude all_devices_info.txt '
              '--exclude .idea/ --exclude static/ --exclude __*__/ --exclude .git/ --exclude *.rar  ./*' % pack_name)
    local('rd /s /q ..\pack_tmp')


def deploy():
    ' 定义一个部署任务 '
    tag = datetime.now()
    print(env.host)
    remote_work_dir = ''
    if env.host == '106.54.217.74':
        remote_work_dir = '/home/ubuntu/hydrology_mgmt/'
    else:
        exit(1)

    remote_tmp_tar = '/tmp/%s' % pack_name
    run('rm -f %s' % remote_tmp_tar)
    # 上传tar文件至远程服务器：
    put(pack_name, remote_tmp_tar)
    # 备份远程服务器工程
    # back_tar_name = '/home/ubuntu/www/backup/cmxsite_backup_%s.tar.gz' % tag
    # run('tar -czvf %s /home/ubuntu/www/cmxsite/*' % back_tar_name)
    # 删除原有工程
    # run('rm -rf /home/ubuntu/www/cmxsite/*')
    # 解压：
    run('tar -xzvf %s -C %s' % (remote_tmp_tar, remote_work_dir))
    run('mv %sother/settings.py %s/hydrology_mgmt/settings.py' % (remote_work_dir, remote_work_dir))
    run('mv %sother/ball_nginx.conf %s/hydrology_mgmt_nginx.conf' % (remote_work_dir, remote_work_dir))
    run('mv %sother/ball_uwsgi.ini %s/hydrology_mgmt_uwsgi.ini' % (remote_work_dir, remote_work_dir))
    run('mv %sother/uwsgi_params %s/uwsgi_params' % (remote_work_dir, remote_work_dir))
    run('rm -rf %sother' % remote_work_dir)
    with cd(remote_work_dir):
        with virtualenv('/home/ubuntu/hydrology_mgmt/kkwork'):
            run('python manage.py makemigrations')
            run('python manage.py migrate')
            run('chmod a+x ./restart.sh')
            run('sh ./restart.sh', pty=False)
            # run('sudo service nginx restart')
            run('sleep 5')
    print(datetime.now()-tag)
