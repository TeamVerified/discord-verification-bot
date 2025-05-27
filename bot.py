import discord
from discord import app_commands
from discord.ext import commands
import random, string, io, os
from captcha.image import ImageCaptcha
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = app_commands.CommandTree(bot)

verified_roles = {}  # guild_id : role_id
captcha_answers = {}

@bot.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {bot.user}")

@tree.command(name="setverifiedrole", description="Set the role to assign after verification.")
@app_commands.describe(role="Role to assign")
async def setverifiedrole(interaction: discord.Interaction, role: discord.Role):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Only admins can set the verified role.", ephemeral=True)
        return
    verified_roles[interaction.guild.id] = role.id
    await interaction.response.send_message(f"Verified role set to {role.name}", ephemeral=True)

@tree.command(name="verify", description="Start verification")
async def verify(interaction: discord.Interaction):
    captcha_text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    captcha_answers[interaction.user.id] = captcha_text

    image = ImageCaptcha()
    data = image.generate(captcha_text)
    file = discord.File(fp=data, filename="captcha.png")

    await interaction.response.send_message(
        "Please type the text in the image below within 60 seconds:",
        file=file
    )

    def check(m):
        return m.author == interaction.user and m.channel == interaction.channel

    try:
        msg = await bot.wait_for("message", timeout=60.0, check=check)
        if msg.content.upper() == captcha_text:
            role_id = verified_roles.get(interaction.guild.id)
            if role_id:
                role = interaction.guild.get_role(role_id)
                await interaction.user.add_roles(role)
                await interaction.followup.send("You have been verified!")
            else:
                await interaction.followup.send("Verified role not set. Ask an admin to run /setverifiedrole.")
        else:
            await interaction.followup.send("Incorrect captcha. Please try again with /verify.")
    except:
        await interaction.followup.send("Timeout. Please try again with /verify.")
