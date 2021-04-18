# 北京大学物院 B116 讨论室预约系统

## 如何部署

### 安装 [poetry](https://github.com/python-poetry/poetry) 并安装项目依赖

#### Windows with Python default to 3.6+

1. 下载脚本 [get-poetry.py](https://github.com/python-poetry/poetry/raw/master/get-poetry.py)
2. 下载 [poetry 最新版](https://github.com/python-poetry/poetry/releases/latest)
3. 运行 `python get-poetry.py --file poetry-<version>-win32.tar.gz`
4. 项目下 `poetry install --no-root`

#### Recent Linux with `python-is-python3` available

1. 安装 `python-is-python3` 包
2. 参照 Windows 安装，记得下载 Linux 对应版本

#### Linux or mac with python default to 2.7

1. 按照 [pyenv 教程安装](https://github.com/pyenv/pyenv#installation)
2. `pyenv install 3.8.5` （请自行替换为适宜版本）
3. `pyenv global 3.8.5`
4. 参照 Windows 安装，记得下载对应版本

#### 不推荐方法（全平台）

如果你确定以后不会 contribute to open source projects which use poetry，并且 `python3 -V` 是 3.6+

1. `pip3 install poetry==1.1.0b2` :tada:

不推荐的原因是如果安装在 Python 3.7，以后要建立 2.7 的环境开发会更麻烦。

### 安装项目依赖

（应该要）重启 shell

```shell
poetry install --no-root
```

如果是生产环境：

```shell
poetry install --no-root --no-dev -E uwsgi
```

> 如果说装 uwsgi 的时候说少 C 编译器，就装个 gcc，没有`<Python.h>`，就装个`python3-dev`


### 安装数据库

怎么安装 MySQL 就不用赘述了吧

#### 准备数据库

数据库名称随意，后续配置匹配即可

显然不能直接用 `newuser@password`，密码太弱了

```sql
-- 这里需要设置编码，保存 emoji 等 Unicode 时需要
CREATE DATABASE PKU_PHY CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;
CREATE DATABASE test_db CHARACTER SET utf8mb4 COLLATE utf8mb4_bin;
CREATE USER 'newuser'@'localhost' IDENTIFIED BY 'password';
-- Version 1
GRANT ALL PRIVILEGES ON * . * TO 'newuser'@'localhost';
-- The asterisks in this command refer to the database and table (respectively) that they can access
-- Version 2
use test_db
GRANT SELECT, INSERT, DELETE ON `test` TO test@'localhost' IDENTIFIED BY 'testy';
-- end if
exit
```

### 设置部分

将 `local.template.yaml` 拷贝为 `local.yaml` 并设置为本地需要的参数。一般需要使用的参数都在其中。

主要修改 `SQLALCHEMY_DATABASE_URI` 和邮件部分。

以下两个值在生产环境中必须要设置

#### SECRET_KEY
```python
>>> import secrets
>>> secrets.token_urlsafe(16)
'Drmhze6EPcv0fN_81Bj-nA'
```

为方便复制粘贴，提供一行版本：

```shell
python -c 'import secrets;print(secrets.token_urlsafe(16))'
```

KEEP THIS REALLY SECRET

#### FERNET_KEY
用来加密 session，学号等。
```python
>>> from cryptography.fernet import Fernet
>>> Fernet.generate_key()
```

为方便复制粘贴，提供一行版本：

```shell
python -c 'from cryptography.fernet import Fernet;print(Fernet.generate_key().decode())'
```

### 本地测试

```shell
# 单纯地跑测试
poetry run pytest # add -s to enable stdout
# 记录测试覆盖率
poetry run task test-cov
poetry run task cov-report
# 代码检查
poetry run task flake8 bookB116
```

### 服务器其他服务部分

仅生产环境需要配置。可参考 [`noc` 脚本](noc)

#### 前端

克隆前端仓库，并安装提示操作。随便把输出文件夹 link 到哪


#### 导入学生数据

```sh
poetry run flask student build student_data1.csv data2.csv
```

如果是迁移，则使用 `mysqldump` 操作

#### 定时任务

```cron
0 10 * * * cd /path/to/bookB116-backend && poetry run flask booking send-summary
```

#### 运行 uWSGI

```sh
export FLASK_ENV=production
export UWSGI_NAME=devphy  # pid, log, sock 的名字
export UWSGI_DEV=1
# 启动
poetry run uwsgi --ini uwsgi.ini
# 重启
poetry run uwsgi --reload "$HOME/.pids/$UWSGI_NAME.pid"
# 关闭
poetry run uwsgi --stop "$HOME/.pids/$UWSGI_NAME.pid"
```

#### Nginx

安装 Nginx 并参考如下配置

```nginx
# /html/vue 为前端 build 好后所在
location / {
    alias /html/vue;
    try_files $uri /index.html;
}
location /api {
    include uwsgi_params;
    uwsgi_pass unix:/tmp/pkuphy.sock;
}
# 无需 test 环境则不用配置
location /test/api {
    rewrite ^/test/(.+) /$1 break;
    include uwsgi_params;
    uwsgi_pass unix:/tmp/devphy.sock;
}
```

## 数据库管理和迁移

#### 初始化数据库

一般在本地使用

```shell
database init
```

一般情况下会同时需要添加开发者的学号，可直接运行一下命令。

```shell
student add 1234567890
```

#### 改变数据库结构？

**本地开发**时不使用 Flask-Migrate，因为本地开发数据库会更加频繁地变动，本地也 migrate 将导致历史混乱。

假设表名为 `TableA`

需要在数据库中先删去该表，再重新建立

```shell
database drop TableA
database init
```

而在**准备上线**时，可以现在测试环境生成数据库迁移脚本

    db migrate -m "Initial migration."

检查脚本，

执行脚本，

    db upgrade

并测试是否正常.

**正式上线**的时候，只需执行脚本即可。

#### 删除数据库表内容

一般来讲本地开发中数据内容需要更新，或者在服务器清除测试数据，会用到。

```shell
database delete TableA
```

#### 推倒重来

一般在本地使用

```shell
database drop-all
database init
```

## 取坏了的名字

#### `booking`

表示预约。众所周知，book 作为动词有预约的意思。为了和“书”做区分，**特地**加上ing

#### `SBLink`

不是SB！（jiu shi）它的全名是`Student-BookRec-Link-Table`

#### `vercode`

`Verification Code`，它居然看起来是一个单词
