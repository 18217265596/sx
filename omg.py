from PIL import Image  # PIL is Pillow
import pyautogui
import keyboard



def get_image():
    def get_left():
        def generate_heroes():
            heroes = []
            hero1 = (340, 229, 237 + 342, 60 + 229)
            heroes.append(hero1)

            for i in range(1, 5):
                hero = (hero1[0], hero1[1] + i * 162, hero1[2], hero1[3] + i * 162)
                heroes.append(hero)

            return heroes

        heroes = generate_heroes()

        def generate_heads():
            heads = []
            herohead1 = (285, 167, 345, 227)
            heads.append(herohead1)

            for i in range(1, 5):
                head = (herohead1[0], herohead1[1] + i * 162, herohead1[2], herohead1[3] + i * 162)
                heads.append(head)

            return heads

        heads = generate_heads()

        def generate_paste_abi():
            abis = []
            abi0 = (40, 80)
            abis.append(abi0)

            for i in range(1, 5):
                abi = (abi0[0], abi0[1] + i * 50)
                abis.append(abi)

            return abis

        abis = generate_paste_abi()

        def generate_paste_heads():
            p_heads = []
            p_head0 = (0, 80)
            p_heads.append(p_head0)

            for i in range(1, 5):
                p_head = (p_head0[0], p_head0[1] + i * 50)
                p_heads.append(p_head)

            return p_heads

        p_heads = generate_paste_heads()

        def crop_and_merge(image_path, heroes, heads, abis, p_heads):
            # 打开图片
            img = Image.open(image_path)

            # 创建新的透明图片
            new_img = Image.new('RGBA', img.size, (0, 0, 0, 0))

            for i in range(len(heroes)):
                # 截取图片
                img_i = img.crop(heroes[i])
                width, height = img_i.size
                img_i = img_i.resize((int(width * 0.6), int(height * 0.6)))

                head_i = img.crop(heads[i])
                width, height = head_i.size
                head_i = head_i.resize((int(width * 0.6), int(height * 0.6)))

                # 将截取的图片粘贴到新图片的对应位置
                new_img.paste(img_i, abis[i])
                new_img.paste(head_i, p_heads[i])

            # return new_img
            # 保存新图片
            new_img.save('left.png', 'PNG')

        # 使用函数
        crop_and_merge('test.jpg', heroes, heads, abis, p_heads)

    get_left()

    def get_right():
        def generate_heroes():
            heroes = []
            hero1 = (1341, 229, 1580, 60 + 229)
            heroes.append(hero1)

            for i in range(1, 5):
                hero = (hero1[0], hero1[1] + i * 162, hero1[2], hero1[3] + i * 162)
                heroes.append(hero)

            return heroes

        heroes = generate_heroes()

        def generate_heads():
            heads = []
            herohead1 = (1575, 167, 1635, 227)
            heads.append(herohead1)

            for i in range(1, 5):
                head = (herohead1[0], herohead1[1] + i * 162, herohead1[2], herohead1[3] + i * 162)
                heads.append(head)

            return heads

        heads = generate_heads()

        def generate_paste_abi():
            abis = []
            abi0 = (1732, 80)
            abis.append(abi0)

            for i in range(1, 5):
                abi = (abi0[0], abi0[1] + i * 50)
                abis.append(abi)

            return abis

        abis = generate_paste_abi()

        def generate_paste_heads():
            p_heads = []
            p_head0 = (1880, 80)
            p_heads.append(p_head0)

            for i in range(1, 5):
                p_head = (p_head0[0], p_head0[1] + i * 50)
                p_heads.append(p_head)

            return p_heads

        p_heads = generate_paste_heads()

        def crop_and_merge(image_path, heroes, heads, abis, p_heads):
            # 打开图片
            img = Image.open(image_path)

            # 创建新的透明图片
            new_img = Image.new('RGBA', img.size, (0, 0, 0, 0))

            for i in range(len(heroes)):
                # 截取图片
                img_i = img.crop(heroes[i])
                width, height = img_i.size
                img_i = img_i.resize((int(width * 0.6), int(height * 0.6)))

                head_i = img.crop(heads[i])
                width, height = head_i.size
                head_i = head_i.resize((int(width * 0.6), int(height * 0.6)))

                # 将截取的图片粘贴到新图片的对应位置
                new_img.paste(img_i, abis[i])
                new_img.paste(head_i, p_heads[i])

            # 保存新图片
            new_img.save('right.png', 'PNG')
            # return new_img

        # 使用函数
        crop_and_merge('test.jpg', heroes, heads, abis, p_heads)

    get_right()

    left = Image.open('left.png').convert('RGBA')
    right = Image.open('right.png').convert('RGBA')

    r, g, b, a = left.split()

    right.paste(left, (0, 0), mask=a)
    right.save('final.png', 'PNG')


def screenshot():
    # 截取全屏并保存为 'test.jpg'
    screenshot = pyautogui.screenshot()
    screenshot.save('test.jpg')


def combined_function():
    screenshot()
    get_image()

# 当按下 'F9' 键时，调用 screenshot 函数
keyboard.add_hotkey('F12', combined_function)

# 开始监听键盘事件
keyboard.wait()
