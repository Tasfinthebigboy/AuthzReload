import discord
import json
import os
from discord.ext import commands

class SelfRolesCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.self_roles_data = self.load_self_roles_data()

    # Load or initialize the JSON database
    def load_self_roles_data(self):
        if not os.path.exists('self_roles_data.json'):
            with open('self_roles_data.json', 'w') as f:
                json.dump({}, f)
        with open('self_roles_data.json', 'r') as f:
            return json.load(f)

    def save_self_roles_data(self, data):
        with open('self_roles_data.json', 'w') as f:
            json.dump(data, f, indent=4)

    # Selfroles setup command
    @discord.app_commands.command(name="selfroles", description="Set up a self-roles system")
    @discord.app_commands.describe(
        description="Description for the self-roles system",
        role1="Role option 1",
        role2="Role option 2",
        role3="Role option 3",
        role4="Role option 4",
        role5="Role option 5",
        role6="Role option 6"
    )
    async def selfroles(self, interaction: discord.Interaction,
                        description: str,
                        role1: discord.Role,
                        role2: discord.Role,
                        role3: discord.Role = None,
                        role4: discord.Role = None,
                        role5: discord.Role = None,
                        role6: discord.Role = None):

        embed = discord.Embed(
            title="Choose your role",
            description=description,
            color=0x00ff00
        )

        buttons = [
            discord.ui.Button(label=role1.name, custom_id=f"role_{role1.id}", style=discord.ButtonStyle.primary),
            discord.ui.Button(label=role2.name, custom_id=f"role_{role2.id}", style=discord.ButtonStyle.primary)
        ]

        if role3:
            buttons.append(discord.ui.Button(label=role3.name, custom_id=f"role_{role3.id}", style=discord.ButtonStyle.primary))
        if role4:
            buttons.append(discord.ui.Button(label=role4.name, custom_id=f"role_{role4.id}", style=discord.ButtonStyle.primary))
        if role5:
            buttons.append(discord.ui.Button(label=role5.name, custom_id=f"role_{role5.id}", style=discord.ButtonStyle.primary))
        if role6:
            buttons.append(discord.ui.Button(label=role6.name, custom_id=f"role_{role6.id}", style=discord.ButtonStyle.primary))

        view = discord.ui.View()
        for button in buttons:
            view.add_item(button)

        await interaction.response.send_message(embed=embed, view=view)
        message = await interaction.original_response()

        # Store role IDs and their corresponding custom IDs
        self.self_roles_data[str(message.id)] = {
            'guild_id': interaction.guild_id,
            'channel_id': interaction.channel_id,
            'roles': {button.custom_id.split('_')[1]: button.custom_id for button in buttons}
        }
        self.save_self_roles_data(self.self_roles_data)

    # Handle interactions for role assignments
    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.component:
            custom_id = interaction.data['custom_id']
            role_id = int(custom_id.split('_')[1])

            guild = self.bot.get_guild(interaction.guild_id)
            role = guild.get_role(role_id)
            member = guild.get_member(interaction.user.id)

            if role and member:
                if role in member.roles:
                    await member.remove_roles(role, reason="Role removed by user.")
                    await interaction.response.send_message(f"Removed the {role.name} role.", ephemeral=True)
                else:
                    await member.add_roles(role, reason="Role added by user.")
                    await interaction.response.send_message(f"Added the {role.name} role.", ephemeral=True)
            else:
                await interaction.response.send_message("Role or member not found.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(SelfRolesCog(bot))
