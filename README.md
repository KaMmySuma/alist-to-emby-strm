# alist-to-emby-strm
一键同步网盘上的节目到本地strm文件以供emby刮削  
灵感来源：https://github.com/xtxt19931207/emby-alist

# 一、前提
配置好的Alist服务端和Emby服务端  
Emby的strm文件应用参考：https://emby.media/support/articles/Strm-Files.html

简单来说就是emby支持将一个仅包含链接的strm文件作为视频源进行刮削，而alist正好可以将网盘视频转化成固定链接，记得在alist全局设置里关闭签名。  
将一些本地剧集上传到网盘，再利用alist提取直链，转化成strm文件，能极大节省本地磁盘空间。

# 二、预期运行结果
### 1. 路径结构同步
在alist挂载的网盘上与本地文件保持相同的文件结构。  
即不改变剧集文件夹的命名方式即文件夹结构，保持相同的`相对路径`从网盘上同步到本地文件夹。

### 2. 文件处理逻辑
- 用于同步的文件夹内存在视频文件，则将提取直链并保存为strm文件，按照原有的文件夹体系保存到本地。
- 如果本地路径已存在strm文件，则进行更新覆盖。
- 如果同级目录下存在同名视频文件，例如`test.strm`同级目录下存在`test.mp4`，则将视频文件移入回收站。即自动删除，因为程序的目的就是利用strm文件替代视频资源。
- 如果是字幕文件或者nfo文件，则直接下载。
- 合集处理
  - 这是我自己的习惯，我会将看过的本地剧集添加到合集【待转换】以标记。  
而在上传到网盘转化成strm文件后，我会将剧集添加到合集【strm文件】以标记。  
  - 程序按照我的习惯进行处理，从网盘同步到本地strm文件时进行查询，如果节目剧集不在合集【strm文件】中，则添加到该合集中；
如果节目剧集在合集【待转换】中，则从该合集中移除并添加到合集【strm文件】中，因为节目会在本次运行后转换成strm文件。
  - 如果不需要可以自行删除合集处理相关代码。
- 循环等待。因为emby实时监控本地文件，经常占用文件，遇到占用时进行循环等待占用结束。

# 三、使用
填好开头几行变量即可。
```py
save_path = r'your_path'  # 要同步到到的本地路径目录
webdav_url = r"http://your_ip:port/dav/path/"  # 要同步到的网盘路径目录，端口号后需要添加/dav/，问就是规则
username = 'your_username'
password = 'your_password'
api_key = 'your_api_key'
temp_collection = 114514  # 【待转】合集id
strm_collection = 191981  # 【strm文件】合集id
```


