import os
import argparse
from PIL import Image
import imagehash
import zipfile

HASH_LENGTH = 64


def get_diff_by_hash(filename1, filename2):
    image1 = Image.open(filename1)
    h1 = imagehash.phash(image1)
    image2 = Image.open(filename2)
    h2 = imagehash.phash(image2)
    return h2 - h1

def clear_dir(path):
    for root, dir, files in os.walk(path):
        for file in files:
            filepath = os.path.join(root, file)
            os.remove(filepath)
        os.rmdir(root)

def unzip_source(source, temp_dir):
    try:
        zip_file = zipfile.ZipFile(source, "r")
        zip_file.extractall(temp_dir)
    except zipfile.BadZipfile as error:
        message = ('Невозможно открыть архив {}. Внутренняя ошибка {}'.
                   format(source, error))
        raise Exception(message)
    finally:
        zip_file.close()


def get_arguments():
    parser = argparse.ArgumentParser(description='Поиск похожих изображений')
    parser.add_argument('source',
                        help='Имя папки или zip/rar архива с изображениями')
    parser.add_argument('sample',
                        help='Имя файла с образцом')
    parser.add_argument('-p', '--password',
                        help='Пароль к архивному файлу')
    parser.add_argument('-o', '--output',
                        help='Имя файла результатов')
    return parser.parse_args()


def check_arguments(args):
    source = args.source
    output = args.output
    temp_dir = ''
    arj_type = None

    source_path = os.path.splitext(source)[0]
    output_path = os.path.split(source)[0]

    if not os.path.exists(source):
        raise IOError('Файл или папка не существует: {}'.format(source))

    if not output:
        output = os.path.join(output_path, 'similarity.txt')

    if os.path.isfile(source):
        temp_dir = source_path
        if zipfile.is_zipfile(source):
            arj_type ='zip'

    return source, output, temp_dir, arj_type


def calculate_similarity(path, sample):
    similarity_list = []
    for root, dirs, files in os.walk(path):
        for current_file in files:
            current_file_path = os.path.join(root, current_file)
            if os.path.isfile(current_file_path):
                hash_distance = get_diff_by_hash(current_file_path, sample)
                similarity = (1-(hash_distance/HASH_LENGTH)) * 100
                similarity_list.append((current_file_path, similarity))

    similarity_list.sort(key=lambda x: x[1], reverse=True)
    return similarity_list


def save_result(source, output_file, result_list):
    with open(output_file, 'w') as file:
        file.write('{}\n'.format(source))
        for image_data in result_list:
            filename = os.path.split(image_data[0])[1]
            file.write('{} --> {:.2f}%\n'.format(filename, image_data[1]))


if __name__ == '__main__':
    args = get_arguments()
    try:
        source, output, temp_dir, arj_type = check_arguments(args)
        if arj_type == 'zip':
            unzip_source(args.source, temp_dir)
        similarity_list = calculate_similarity(temp_dir, args.sample)
        save_result(source, output, similarity_list)
    except IOError as error:
        print(error)

    except FileNotFoundError as error:
        print(error)

    except Exception as error:
        print(error)

    finally:
        if temp_dir:
            clear_dir(temp_dir)



