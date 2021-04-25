import functools
import importlib
import io
import math
import os
import typing

import discord
import humanize
from discord.ext import commands
from discord.ext import flags
from PIL import Image

import common.image_utils as image_utils
import common.utils as utils


class ImageCMDs(commands.Cog, name="Image"):
    """A series of commands for manipulating images in certain ways."""

    def __init__(self, bot):
        self.bot = bot

    def get_size(self, image: io.BytesIO):
        old_pos = image.tell()
        image.seek(0, os.SEEK_END)
        size = image.tell()
        image.seek(old_pos, os.SEEK_SET)

        return size

    def pil_compress(self, image, ext, flags):
        pil_image = Image.open(image)
        compress_image = io.BytesIO()

        try:
            if (
                flags["ori_ext"] in ("gif", "webp")
                and ext not in ("gif", "webp")
                and pil_image.is_animated
            ):
                raise commands.BadArgument(
                    "Cannot convert an animated image to this file type!"
                )

            if flags["shrink"]:
                width = pil_image.width
                height = pil_image.height

                if width > 1920 or height > 1920:
                    bigger = width if width > height else height
                    factor = math.ceil(bigger / 1920)
                    pil_image = pil_image.reduce(factor=factor)

            if ext == "jpeg":
                if pil_image.mode != "RGB":
                    pil_image = pil_image.convert("RGB")
                pil_image.save(
                    compress_image, format=ext, quality=flags["quality"], optimize=True
                )
            elif ext in ("gif", "png"):
                pil_image.save(compress_image, format=ext, optimize=True)
            elif ext == "webp":
                pil_image.save(
                    compress_image,
                    format=ext,
                    minimize_size=True,
                    quality=flags["quality"],
                )
            else:
                compress_image.close()
                raise commands.BadArgument("Invalid file type!")

            compress_image.seek(0, os.SEEK_SET)

            return compress_image

        except BaseException:
            compress_image.close()
            raise

    @flags.command()
    @flags.add_flag("-shrink", "--shrink", type=bool, default=True)
    @flags.add_flag("-format", "--format", type=str, default="default")
    @flags.add_flag("-quality", "--quality", default=70, type=int)
    async def compress(
        self, ctx, url: typing.Optional[image_utils.URLToImage], **flags
    ):
        """Compresses down the image given.
        It must be an image of type GIF, JPG, PNG, or WEBP. It must also be under 8 MB.
        Image quality will take a hit, and the image will shrink down if it's too big (unless you specify to not shrink the image).
        Flags --shrink <true/false> (specifies to shrink the image - it will by default)
        --format <format> (converts the image to the specified format, and it must be 'gif, jpg, png, or webp' \
        - the resulting image will be in the same format as the original by default)
        --quality <number> (specifies quality from 0-100, only works with JPG and WEBP files, default is 70)"""

        if flags["format"] == "default":
            img_format = "default"
        else:
            img_type_checker = image_utils.ImageTypeChecker
            img_format = await img_type_checker.convert(
                img_type_checker, ctx, flags["format"]
            )

        if not 0 <= flags["quality"] <= 100:
            raise commands.BadArgument("Quality must be a number between 0-100!")

        if not url:
            url = image_utils.image_from_ctx(ctx)

        async with ctx.channel.typing():
            image_data = await image_utils.get_file_bytes(
                url, 8388608, equal_to=False
            )  # 8 MiB

            try:
                ori_image = io.BytesIO(image_data)

                mimetype = discord.utils._get_mime_type_for_image(image_data)
                ext = mimetype.split("/")[1]
                flags["ori_ext"] = ext

                if img_format != "default":
                    ext = flags["format"]

                compress = functools.partial(self.pil_compress, ori_image, ext, flags)
                compress_image = await self.bot.loop.run_in_executor(None, compress)

                ori_size = self.get_size(ori_image)
                compressed_size = self.get_size(compress_image)

            finally:
                ori_image.close()

            try:
                com_img_file = discord.File(compress_image, f"image.{ext}")

                content = (
                    f"Original Size: {humanize.naturalsize(ori_size, binary=True)}\n"
                    + f"Reduced Size: {humanize.naturalsize(compressed_size, binary=True)}\n"
                    + f"Size Saved: {round(((1 - (compressed_size / ori_size)) * 100), 2)}%"
                )
            except BaseException:
                compress_image.close()
                raise

            await ctx.reply(content=content, file=com_img_file)

    @flags.command(aliases=["image_convert"])
    @flags.add_flag("-shrink", "--shrink", type=bool, default=False)
    @flags.add_flag("-quality", "--quality", default=80, type=int)
    async def img_convert(
        self,
        ctx,
        url: typing.Optional[image_utils.URLToImage],
        img_type: image_utils.ImageTypeChecker,
        **flags,
    ):
        """Converts the given image into the specified image type.
        Both the image and the specified image type must be of type GIF, JP(E)G, PNG, or WEBP. The image must also be under 8 MB.
        Flags: --shrink <true/false> (specifies to shrink the image - it won't by default)
        --quality <number> (specifies quality from 0-100, only works with JPG and WEBP files, default is 80)"""

        if not 0 <= flags["quality"] <= 100:
            raise commands.BadArgument("Quality must be a number between 0-100!")

        if not url:
            url = image_utils.image_from_ctx(ctx)

        async with ctx.channel.typing():
            image_data = await image_utils.get_file_bytes(
                url, 8388608, equal_to=False
            )  # 8 MiB
            ori_image = io.BytesIO(image_data)

            mimetype = discord.utils._get_mime_type_for_image(image_data)
            flags["ori_ext"] = mimetype.split("/")[1]
            ext = img_type

            compress = functools.partial(self.pil_compress, ori_image, ext, flags)
            converted_image = await self.bot.loop.run_in_executor(None, compress)

            ori_image.close()

            try:
                convert_img_file = discord.File(converted_image, f"image.{ext}")
            except BaseException:
                converted_image.close()
                raise

            await ctx.reply(file=convert_img_file)


def setup(bot):
    importlib.reload(utils)
    importlib.reload(image_utils)

    bot.add_cog(ImageCMDs(bot))
