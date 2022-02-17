"""Модуль распаковщика zip архивов."""

from os import path, listdir, mkdir, rename, remove
from shutil import rmtree
from zipfile import ZipFile

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import InMemoryUploadedFile

from .utils import random_string


class UnpackZip:
    """Распаковщик zip архивов."""

    def __init__(self, archive: InMemoryUploadedFile):
        """Конструктор распаковщика zip архивов.

        :param archive: zip архив
        """
        self.archive = archive
        self.folder_name = random_string(10)
        self.tmp_dir = path.join(settings.BASE_DIR, 'storage', self.folder_name)
        mkdir(self.tmp_dir)
        archive_name: str = path.join(self.tmp_dir, self.archive.name)
        with open(archive_name, 'wb') as fl:
            for chunk in self.archive.chunks():
                fl.write(chunk)
        with ZipFile(archive_name) as zf:
            for file_name in zf.namelist():
                try:
                    zf.extract(file_name, self.tmp_dir)
                    try:
                        ed_name = self._get_right_file_name(file_name)
                        rename(path.join(self.tmp_dir, file_name), path.join(self.tmp_dir, ed_name))
                    except UnicodeEncodeError as _:
                        # Если удалось преобразовать, ничего не делаем
                        pass
                except OSError as e:
                    raise ValidationError({
                        'name': [f'Слишком длинное название файла {self._get_right_file_name(file_name)}.']
                    })
        remove(archive_name)

    def __call__(self) -> list[str]:
        """Получение имен файлов."""

        return [path.join(self.tmp_dir, file_name) for file_name in listdir(self.tmp_dir)]

    def __del__(self):
        """Удаление временной папки."""

        rmtree(self.tmp_dir)

    @classmethod
    def _get_right_file_name(cls, file_name: str) -> str:
        """Получение правильного имени файла при загрузке с Windows.

        :param: file_name: неправильное имя файла
        :return: правильное имя файла
        """

        try:
            return file_name.encode('cp437').decode('cp866')
        except UnicodeEncodeError as _:
            # Если удалось преобразовать, ничего не делаем
            return file_name
