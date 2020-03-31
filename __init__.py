# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

# ----------------------------------------------------------
# Author: Cody Winchester (codywinch)
# ----------------------------------------------------------

# ----------------------------------------------
# Define Addon info
# --

bl_info = {
    "name": "Abnormal",
    "author": "Cody Winchester (codywinch)",
    "version": (1, 0),
    "blender": (2, 80, 0),
    "location": "3D View > Object and Properties > Object tab",
    "description": "BNPR Normal Editing Tools",
    "warning": "",
    "wiki_url": "",
    "category": "3D View"
    }



import bpy
from bpy.props import *
from .ui import *
from .properties import *
from .operators_modal import *
from .classes import *



classes = [
    ABN_OT_normal_editor_modal,
    ABN_OT_copy_basis_sk_normals,
    AbnormalAddonPreferences,
    ABNScnProperties,
    ABN_PT_abnormal_panel,
]


def register():
    for c in classes:
        bpy.utils.register_class(c)
    
    bpy.types.Scene.abnormal_props = PointerProperty(type=ABNScnProperties)


def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)
    
    del bpy.types.Scene.abnormal_props

if __name__ == "__main__":
    register()
