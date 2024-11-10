import os
import requests
import time
import json
from send2trash import send2trash
import traceback
from webdav3.client import Client

save_path = r'your_path'  # 要同步到到的本地路径目录
webdav_url = r"http://your_ip:port/dav/path/"  # 要同步到的网盘路径目录
emby_url = r"http://localhost:8096"  # emby链接和端口
username = 'your_username'
password = 'your_password'
api_key = 'your_api_key'
temp_collection = 114514  # 【待转】合集id
strm_collection = 191981  # 【strm文件】合集id

result = {}
video_extensions = (
    '.mp4',  # MPEG-4
    '.mkv',  # Matroska
    '.avi',  # Audio Video Interleave
    '.mov',  # QuickTime
    '.ts',  # Transport Stream
    '.flv',  # Flash Video
    '.wmv',  # Windows Media Video
    '.m4v',  # MPEG-4 Video
    '.3gp',  # 3GPP Multimedia
    '.webm',  # WebM Video
    '.vob',  # Video Object (DVD)
    '.ogv',  # Ogg Video
    '.rm',  # RealMedia
    '.rmvb',  # RealMedia Variable Bitrate
    '.asf',  # Advanced Systems Format
    '.mpeg',  # MPEG Video
    '.mpg',  # MPEG Video
    '.f4v',  # Flash MP4 Video
    '.divx',  # DivX Video
    '.xvid',  # Xvid Video
    '.mxf',  # Material eXchange Format
    '.mts',  # AVCHD Video
    '.m2ts',  # Blu-ray Disc Audio-Video
    '.dv',  # Digital Video
    '.h264',  # H.264 Encoded Video
    '.hevc',  # High Efficiency Video Coding (H.265)
    '.amv',  # Anime Music Video
    '.svi',  # Samsung Video
    '.bik',  # Bink Video
    '.nsv',  # Nullsoft Streaming Video
)
# 颜色代码
# 前景色 (文字颜色)
BLACK = "\033[30m"  # 黑色
RED = "\033[31m"  # 红色
GREEN = "\033[32m"  # 绿色
YELLOW = "\033[33m"  # 黄色
BLUE = "\033[34m"  # 蓝色
MAGENTA = "\033[35m"  # 洋红色
CYAN = "\033[36m"  # 青色
WHITE = "\033[37m"  # 白色
RESET = "\033[0m"  # 重置颜色


def get_item_from_collection(item_id):
    # 获取指定合集内容
    url = f'{emby_url}/emby/Items?api_key={api_key}&ParentId={item_id}'
    response = requests.get(url)
    return response.json()


def collections_remove_item(collection_id, item_id):
    # 从指定合集删除指定节目
    url = f'{emby_url}/emby/Collections/{collection_id}/Items/Delete?Ids={item_id}&api_key={api_key}'
    response = requests.post(url)
    return response.status_code


def collections_add_item(collection_id, item_id):
    # 向指定合集添加指定节目
    url = f'{emby_url}/emby/Collections/{collection_id}/Items?Ids={item_id}&api_key={api_key}'
    response = requests.post(url)
    return response.status_code


def get_itemid_from_path(path):
    # 获取指定路径的ID
    url = f'{emby_url}/emby/Items?api_key={api_key}&Recursive=true&Fields=Path&Filters=IsFolder&Path={path}'
    try:
        response = requests.get(url)
        collections = response.json()
        if collections["Items"][0]["Type"] != "Folder":
            return [collections["Items"][0]["Id"]]
        else:
            folder_item_json = get_item_from_collection(collections["Items"][0]["Id"])
            folder_item_list = []
            for item in folder_item_json["Items"]:
                folder_item_list.append(item["Id"])
            print(f"从文件夹提取到节目ID：{folder_item_list}")
            return folder_item_list
    except IndexError:
        print(f"获取ID——{path}：{CYAN}未获取到路径节目信息，将跳过合集处理，待刮削数据后再次运行即可{RESET}")
    except Exception as e:
        print(f"{MAGENTA}获取ID——{path}：发生了意外错误，未获取到路径节目信息\n错误信息：{e}{RESET}")
        traceback.print_exc()
        return


def list_files(webdav_url_, username_, password_, current_path):
    # 创建WebDAV客户端
    options = {
        'webdav_hostname': webdav_url_,
        'webdav_login': username_,
        'webdav_password': password_
    }
    client = Client(options)
    folder_list_ = []
    file_list_ = []
    q = 1
    while q < 15:
        try:
            # 获取WebDAV服务器上的文件列表
            files = client.list()
        except:
            q += 1
            print('连接失败，1秒后重试...')
            time.sleep(1)
        else:
            if q > 1:
                print('重连成功...')
            break
    for file in files[1:]:
        # 如果是文件夹，递归调用
        if file[-1] == '/':
            folder_list_.append(file)
            sub_folder_list, sub_file_list = list_files(webdav_url_ + file, username_, password_, current_path + file)
            file_list_.extend(sub_file_list)
            folder_list_.extend(sub_folder_list)
        # 如果是文件
        else:
            if os.path.splitext(file)[1].lower() in video_extensions:
                # 如果是视频文件，添加到字典
                file_list_.append(webdav_url_.replace('/dav/', '/d/') + file)
                base = os.path.splitext(current_path + file)[0]
                result[os.path.normpath(base + ".strm")] = webdav_url_.replace('/dav/', '/d/') + file

            elif os.path.splitext(file)[1].lower() in ['.nfo']:
                # 如果是nfo，且本地不存在，则下载到本地
                if not os.path.exists(current_path + file):
                    url = webdav_url_.replace('/dav/', '/d/') + file
                    response = requests.get(url)
                    print(f"{GREEN}下载nfo：{current_path + file}{RESET}")
                    n = 1
                    while True:
                        try:
                            os.makedirs(os.path.dirname(current_path + file), exist_ok=True)
                            with open(current_path + file, 'wb') as fl:
                                fl.write(response.content)
                            break
                        except PermissionError:
                            print(f"写入nfo——{RED}文件{current_path + file}被占用,等待 2 秒后进行第 {n} 次重试{RESET}")
                            time.sleep(2)
                            n += 1
                        except Exception as err:
                            print("意料之外的错误：", err)
                            # 输出详细的异常信息（堆栈跟踪）
                            traceback.print_exc()
                            break
            elif os.path.splitext(file)[1].lower() in ['.ass', '.srt', '.ssa', '.sub', '.idx', '.vtt', '.dfxp', '.xml', '.sbv', '.mpl2', '.lrc', '.txt']:
                # 如果是字幕，且本地不存在，则下载到本地
                if not os.path.exists(current_path + file):
                    url = webdav_url_.replace('/dav/', '/d/') + file
                    response = requests.get(url)
                    print(f"{GREEN}下载字幕：{current_path + file}{RESET}")
                    n = 1
                    while True:
                        try:
                            os.makedirs(os.path.dirname(current_path + file), exist_ok=True)
                            with open(current_path + file, 'wb') as fl:
                                fl.write(response.content)
                            break
                        except PermissionError:
                            print(f"写入字幕——{RED}文件{current_path + file}被占用,等待 2 秒后进行第 {n} 次重试{RESET}")
                            time.sleep(2)
                            n += 1
                        except Exception as err:
                            print("意料之外的错误：", err)
                            # 输出详细的异常信息（堆栈跟踪）
                            traceback.print_exc()
                            break
    return folder_list_, file_list_


# 获取待转合集ID
temp_item_json = get_item_from_collection(temp_collection)
temp_item_list = []
for i in temp_item_json["Items"]:
    temp_item_list.append(i["Id"])
if temp_item_list:
    print(f"获取待转ID成功：{temp_item_list}")

# 获取strm合集ID
strm_item_json = get_item_from_collection(strm_collection)
strm_item_list = []
for i in strm_item_json["Items"]:
    strm_item_list.append(i["Id"])
if strm_item_list:
    print(f"获取strm ID成功：{strm_item_list}")

directory_list = []
list_files(webdav_url, username, password, save_path)
for i in result:
    # 处理合集
    # 从根目录向后提取四层目录
    parts = os.path.normpath(i).split(os.sep)  # 规范化路径并按分隔符拆分
    # 确保有足够的层级，并提取前四层
    if len(parts) >= 4:
        # 重新组合前三个子文件夹
        directory = os.sep.join(parts[:4])

        # 如果该目录未经过合集处理，则进行合集处理
        if directory not in directory_list:
            directory_list.append(directory)
            # 通过目录获取节目ID
            item_id_list = get_itemid_from_path(directory)

            if item_id_list:  # 如果获取到ID
                for item_id in item_id_list:
                    # 如果ID在待转合集中，则移出
                    if item_id in temp_item_list:
                        r_code = collections_remove_item(temp_collection, item_id)
                        if r_code == 200 or r_code == 204:
                            print(f"{YELLOW}从待转合集中移除节目：{parts[3]}{RESET}")
                        else:
                            print(f"{RED}移除节目{parts[3]}时返回意外状态：{r_code}{RESET}")

                    # 如果ID不在strm合集中，则添加节目到strm合集
                    if item_id not in strm_item_list:
                        r_code = collections_add_item(strm_collection, item_id)
                        if r_code == 200 or r_code == 204:
                            print(f"{GREEN}添加节目到strm合集：{parts[3]}{RESET}")
                        else:
                            print(f"{RED}添加节目{parts[3]}时返回意外状态：{r_code}{RESET}")

    else:
        print(f"{RED}没有足够的层级：{i}{RESET}")

    # 操作strm文件
    if not os.path.exists(i):
        # 创建目录（如果不存在）
        os.makedirs(os.path.dirname(i), exist_ok=True)
        number = 1
        while True:
            try:
                with open(i, 'w', encoding='utf-8') as f:
                    f.write(result[i])
                print(f"{GREEN}创建文件：{i}{RESET}")
                break
            except PermissionError:
                print(f"执行创建——{RED}文件{i}被占用,等待 2 秒后进行第 {number} 次重试{RESET}")
                time.sleep(2)
                number += 1
            except Exception as e:
                print("意料之外的错误：", e)
                # 输出详细的异常信息（堆栈跟踪）
                traceback.print_exc()
                break
    else:
        number = 1
        while True:
            try:
                with open(i, 'w', encoding='utf-8') as f:
                    f.write(result[i])
                print(f"更新文件：{i}")
                break
            except PermissionError:
                print(f"执行更新——{RED}文件{i}被占用,等待 2 秒后进行第 {number} 次重试{RESET}")
                time.sleep(2)
                number += 1
            except Exception as e:
                print("意料之外的错误：", e)
                # 输出详细的异常信息（堆栈跟踪）
                traceback.print_exc()
                break

    # 删除同名视频文件
    for ext in video_extensions:
        file = os.path.splitext(i)[0] + ext
        if os.path.exists(file):
            while True:
                try:
                    send2trash(file)
                    print(f"{YELLOW}删除文件：{file}{RESET}")
                    break
                except PermissionError:
                    print(f"执行删除——{RED}文件{i}被占用,等待 2 秒后进行第 {number} 次重试{RESET}")
                    time.sleep(2)
                    number += 1
                except Exception as e:
                    print("意料之外的错误：", e)
                    # 输出详细的异常信息（堆栈跟踪）
                    traceback.print_exc()
                    break

