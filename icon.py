# 这段程序可将图标app.ico转换成icon.py文件里的base64数据
# 先运行此程序

import base64
open_icon = open("app.ico","rb")
b64str = base64.b64encode(open_icon.read())
open_icon.close()
write_data = "img=%s" % b64str
f = open("icon.py","w+")
f.write(write_data)
f.close()