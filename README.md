# 📱 iOS 文件接收服务器

基于 Flask 的局域网 HTTP 文件接收服务器：iPhone / iPad 通过「快捷指令」或任意 HTTP 客户端把照片、视频、文件传到 Windows 电脑，并可在网页上直接预览图片与视频。

## 界面预览

![网页界面预览](docs/screenshot.png)

## 功能

- ✅ 接收 multipart 表单上传 / 原始 body 上传（单文件最大 2GB）
- ✅ 网页端：上传测试、图片缩略图、视频首帧预览、点击放大灯箱播放、下载、删除
- ✅ 同名文件自动加时间戳防覆盖，文件名安全过滤
- ✅ REST 接口：列表 / 下载 / 删除

## 环境要求

- Python 3.10+（已装 Flask 即可跳过下一步）

```powershell
pip install -r requirements.txt
```

## 如何运行

方式一：命令行

```powershell
python app.py
```

方式二：双击桌面上的「ios传输专用.bat」批处理（关闭黑色窗口即停止服务）。

启动后控制台会显示本机局域网 IP，例如：

```
iOS 上传地址: http://192.168.232.104:8900/upload
```

- 服务器监听 `0.0.0.0:8900`，改端口只需修改 `app.py` 顶部的 `PORT = 8900`
- 收到的文件保存在 `uploads\` 目录
- 电脑浏览器打开 `http://127.0.0.1:8900` 可查看/预览已接收的文件

## 如何配置 iOS 手机

前提：iPhone 与电脑连接**同一个 Wi-Fi / 局域网**。

### 方法一：快捷指令（推荐）

1. 打开 iPhone 上的「快捷指令」App → 新建快捷指令，命名为如「传到电脑」
2. 添加操作 **「获取文件」**（若要传照片/视频，可改用「选取照片」）
3. 添加操作 **「获取 URL 的内容」**，配置为：
   - 方法：**POST**
   - URL：`http://<电脑IP>:8900/upload`（IP 以服务器启动时显示的为准）
   - 展开「请求体」→ 请求体类型选「文件」→ 选择上一步的「文件」变量
4. （可选）关闭「包含响应」，避免每次弹出返回结果
5. 运行快捷指令，选择文件即完成上传；还可以勾选「显示在"共享"表中」，以后在相册/文件 App 里点「共享 → 传到电脑」直接发送

### 方法二：原始 body 上传（适合 App / 脚本）

把文件二进制直接作为请求体，用 Header 指定保存的文件名：

```bash
curl -X POST -H "X-Filename: photo.jpg" --data-binary @photo.jpg http://192.168.232.104:8900/upload
```

## HTTP 接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/` | 网页首页（上传 + 预览） |
| POST / PUT | `/upload` | 接收文件 |
| GET | `/files` | JSON 文件列表 |
| GET | `/files/<名称>` | 下载文件 |
| GET | `/preview/<名称>` | 内联预览（图片/视频） |
| DELETE | `/files/<名称>` | 删除文件 |

## 常见问题

- **iPhone 连不上**：确认两者在同一局域网；Windows 防火墙需放行 8900 端口（首次运行弹窗时选「专用网络允许」），或手动添加规则：
  ```powershell
  New-NetFirewallRule -DisplayName "iOS File Server" -Direction Inbound -LocalPort 8900 -Protocol TCP -Action Allow -Profile Private
  ```
- **HEIC 照片网页里显示不出来**：Windows 版 Chrome/Edge 可能不支持 HEIC，页面会显示占位图标，点击后仍可下载原图
- **电脑 IP 变了**：以服务器启动时控制台显示的地址为准
