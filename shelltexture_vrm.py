bl_info = {
    "name": "VRM Hair/Fur Shell Texturing",
    "author": "Meringue Rouge",
    "version": (1, 0),
    "blender": (4, 2, 0),
    "location": "View 3D > UI > VRM",
    "description": "Shell texturing for VRM hair and fur with MToon materials and per-material control",
    "category": "Object",
    "website": "https://github.com/Meringue-Rouge/VRM-Fur-Shell-Texturing"
}

import bpy
import random

# ------------------------------------------------------------
# Material checkbox item
# ------------------------------------------------------------

class VRMShellMaterialItem(bpy.types.PropertyGroup):
    material: bpy.props.PointerProperty(type=bpy.types.Material)
    use_shell: bpy.props.BoolProperty(default=True)


# ------------------------------------------------------------
# Sync material list (manual)
# ------------------------------------------------------------

def sync_material_list(obj):
    if not obj or obj.type != 'MESH':
        return

    obj.vrm_shell_materials.clear()
    for mat in obj.data.materials:
        item = obj.vrm_shell_materials.add()
        item.material = mat
        item.use_shell = True


# ------------------------------------------------------------
# Operator: Sync Materials
# ------------------------------------------------------------

class SyncMaterialsOperator(bpy.types.Operator):
    bl_idname = "object.sync_shell_materials"
    bl_label = "Refresh Material List"
    bl_options = {'REGISTER', 'UNDO'}
    bl_description = "Update the material list from the active object"

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "Select a mesh object.")
            return {'CANCELLED'}
        
        sync_material_list(obj)
        self.report({'INFO'}, f"Material list updated: {len(obj.vrm_shell_materials)} materials found")
        return {'FINISHED'}


# ------------------------------------------------------------
# Helper: Enable MToon for material
# ------------------------------------------------------------

def enable_mtoon_material(material):
    """Enable VRM MToon material properties without outline"""
    try:
        material.vrm_addon_extension.mtoon1.enabled = True
        material.vrm_addon_extension.mtoon1.alpha_mode = 'BLEND'
        material.vrm_addon_extension.mtoon1.transparent_with_z_write = False
        material.vrm_addon_extension.mtoon1.extensions.vrmc_materials_mtoon.outline_width_mode = 'none'
        material.vrm_addon_extension.mtoon1.extensions.vrmc_materials_mtoon.outline_width_factor = 0.0
        return True
    except:
        return False


# ------------------------------------------------------------
# Helper: Create modified texture with random pixels deleted and noise multiplied
# ------------------------------------------------------------

def create_shell_texture(base_image, shell_name, deletion_ratio=0.75, noise_image=None, noise_vals=None, pattern='RANDOM'):
    """Create a new texture based on the original with random pixels deleted and optional noise alpha multiplication"""
    if not base_image:
        return None
    
    # Create new image with same dimensions
    width, height = base_image.size
    new_img = bpy.data.images.new(
        name=shell_name,
        width=width,
        height=height,
        alpha=True
    )
    
    total_pixels = width * height
    
    # Get original pixels
    original_pixels = list(base_image.pixels)
    
    # Determine if base has alpha
    has_alpha = (len(original_pixels) == 4 * total_pixels)
    
    # Prepare noise if provided
    noise_pixels = None
    noise_width = noise_height = 0
    if noise_image:
        noise_pixels = list(noise_image.pixels)
        noise_width, noise_height = noise_image.size
    
    # Prepare new pixels
    new_pixels = [0.0] * (4 * total_pixels)
    
    for i in range(total_pixels):
        x = i % width
        y = i // width
        
        # Get original color and alpha
        if has_alpha:
            r = original_pixels[i*4]
            g = original_pixels[i*4+1]
            b = original_pixels[i*4+2]
            alpha = original_pixels[i*4+3]
        else:
            r = original_pixels[i*3]
            g = original_pixels[i*3+1]
            b = original_pixels[i*3+2]
            alpha = 1.0
        
        # Get noise alpha if available, but only for random pattern
        noise_alpha = 1.0
        if pattern == 'RANDOM' and noise_pixels and noise_width > 0 and noise_height > 0:
            noise_x = x % noise_width
            noise_y = y % noise_height
            noise_i = (noise_y * noise_width + noise_x) * 4 + 3
            noise_alpha = noise_pixels[noise_i]
        
        # Multiply alpha by noise
        alpha *= noise_alpha
        
        # Apply deletion
        rand_val = noise_vals[i] if noise_vals else random.random()
        if rand_val < deletion_ratio:
            alpha = 0.0
        
        # Apply vertical fade if applicable
        if pattern == 'VERTICAL' and alpha > 0:
            strand_height = 10
            fade_length = 4
            offset = int(rand_val * strand_height)
            y_mod = (y + offset) % strand_height
            fade_start = strand_height - fade_length
            if y_mod >= fade_start:
                fade_pos = y_mod - fade_start
                fade = 1.0 - (fade_pos / fade_length)
                alpha *= fade
        
        # Set color to 0 if alpha == 0
        if alpha == 0.0:
            r = g = b = 0.0
        
        new_pixels[i*4] = r
        new_pixels[i*4+1] = g
        new_pixels[i*4+2] = b
        new_pixels[i*4+3] = alpha
    
    # Apply modified pixels
    new_img.pixels = new_pixels
    new_img.pack()
    
    return new_img


# ------------------------------------------------------------
# Operator
# ------------------------------------------------------------

class ShellTexturingOperator(bpy.types.Operator):
    bl_idname = "object.add_shell_texturing"
    bl_label = "Add Shell Texturing (MToon)"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "Select a mesh object.")
            return {'CANCELLED'}

        checked_indices = [
            i for i, item in enumerate(obj.vrm_shell_materials)
            if item.use_shell and item.material
        ]

        if not checked_indices:
            self.report({'ERROR'}, "No materials enabled.")
            return {'CANCELLED'}

        layers = context.scene.shell_layers
        pattern = context.scene.shell_texture_pattern

        # ------------------------------------------------------------
        # Noise image (binary, alpha only)
        # ------------------------------------------------------------

        img_name = "VRMHairNoise"
        if img_name not in bpy.data.images:
            img = bpy.data.images.new(img_name, 512, 512)
            pixels = []
            for _ in range(512 * 512):
                v = 1.0 if random.random() < 0.25 else 0.0
                pixels.extend((1.0, 1.0, 1.0, v))  # white color, alpha only
            img.pixels = pixels
            img.pack()
        else:
            img = bpy.data.images[img_name]

        # ------------------------------------------------------------
        # Create shell materials (MToon) - one per layer
        # ------------------------------------------------------------

        shell_mats = {}  # idx: [mat_layer0, mat_layer1, ...]
        slot_starts = {}  # idx: start_slot for its shell mats

        for idx in checked_indices:
            base = obj.data.materials[idx]
            base_image = None
            try:
                base_image = base.vrm_addon_extension.mtoon1.pbr_metallic_roughness.base_color_texture.index.source
            except:
                pass

            if not base_image:
                # Use base color factor to create temp image
                base_color = base.vrm_addon_extension.mtoon1.pbr_metallic_roughness.base_color_factor
                temp_name = "Temp_Base_" + base.name
                if temp_name in bpy.data.images:
                    base_image = bpy.data.images[temp_name]
                else:
                    base_image = bpy.data.images.new(temp_name, 512, 512, alpha=True)
                    pixels = []
                    r, g, b, a = base_color
                    for _ in range(512 * 512):
                        pixels.extend((r, g, b, a))
                    base_image.pixels = pixels
                    base_image.pack()

            width, height = base_image.size
            total_pixels = width * height

            # Generate shared noise_vals for nested deletion
            if pattern == 'VERTICAL':
                random_per_x = [random.random() for _ in range(width)]
                noise_vals = [0.0] * total_pixels
                for i in range(total_pixels):
                    x = i % width
                    noise_vals[i] = random_per_x[x]
            else:
                noise_vals = [random.random() for _ in range(total_pixels)]

            shell_list = []
            for layer in range(layers):
                name = f"Shell_{base.name}_{layer}"
                if name in bpy.data.materials:
                    shell = bpy.data.materials[name]
                else:
                    shell = base.copy()
                    shell.name = name

                enable_mtoon_material(shell)

                layer_frac = layer / (layers - 1.0) if layers > 1 else 0.0
                deletion_ratio = 0.85 * layer_frac  # Adjust max deletion as needed

                shell_texture_name = f"ShellTex_{base.name}_{layer}"

                if shell_texture_name in bpy.data.images:
                    shell_img = bpy.data.images[shell_texture_name]
                else:
                    shell_img = create_shell_texture(base_image, shell_texture_name, deletion_ratio=deletion_ratio, noise_image=img, noise_vals=noise_vals, pattern=pattern)

                if shell_img:
                    try:
                        shell.vrm_addon_extension.mtoon1.pbr_metallic_roughness.base_color_texture.index.source = shell_img
                    except:
                        pass

                # Set blend method
                shell.blend_method = 'BLEND'

                shell_list.append(shell)

            shell_mats[idx] = shell_list

        # ------------------------------------------------------------
        # Add shell materials to object slots
        # ------------------------------------------------------------

        current_slot = len(obj.data.materials)
        for idx in checked_indices:
            slot_starts[idx] = current_slot
            for shell_mat in shell_mats[idx]:
                obj.data.materials.append(shell_mat)
            current_slot += layers

        # ------------------------------------------------------------
        # Geometry Nodes
        # ------------------------------------------------------------

        group_name = "VRM_ShellFurSystem"
        if group_name in bpy.data.node_groups:
            gn = bpy.data.node_groups[group_name]
            gn.nodes.clear()
        else:
            gn = bpy.data.node_groups.new(group_name, 'GeometryNodeTree')

        nodes = gn.nodes
        links = gn.links

        iface = gn.interface

        iface.new_socket(
            name="Geometry",
            description="",
            in_out='INPUT',
            socket_type='NodeSocketGeometry'
        )

        iface.new_socket(
            name="Layers",
            description="",
            in_out='INPUT',
            socket_type='NodeSocketInt'
        ).default_value = context.scene.shell_layers

        iface.new_socket(
            name="Thickness",
            description="",
            in_out='INPUT',
            socket_type='NodeSocketFloat'
        ).default_value = 0.005

        iface.new_socket(
            name="Geometry",
            description="",
            in_out='OUTPUT',
            socket_type='NodeSocketGeometry'
        )

        gin = nodes.new("NodeGroupInput")
        gout = nodes.new("NodeGroupOutput")

        join_final = nodes.new("GeometryNodeJoinGeometry")
        links.new(gin.outputs["Geometry"], join_final.inputs["Geometry"])

        for idx in checked_indices:
            mat_index = nodes.new("GeometryNodeInputMaterialIndex")
            compare = nodes.new("FunctionNodeCompare")
            compare.data_type = 'INT'
            compare.operation = 'EQUAL'
            compare.inputs[3].default_value = idx

            sep = nodes.new("GeometryNodeSeparateGeometry")
            links.new(gin.outputs["Geometry"], sep.inputs["Geometry"])
            links.new(compare.outputs["Result"], sep.inputs["Selection"])
            links.new(mat_index.outputs[0], compare.inputs[2])

            repeat_in = nodes.new("GeometryNodeRepeatInput")
            repeat_out = nodes.new("GeometryNodeRepeatOutput")
            repeat_out.repeat_items.new("GEOMETRY", "Accum")
            repeat_out.repeat_items.new("GEOMETRY", "Src")
            repeat_in.pair_with_output(repeat_out)

            links.new(sep.outputs["Selection"], repeat_in.inputs["Src"])
            links.new(gin.outputs["Layers"], repeat_in.inputs["Iterations"])

            # Offset = (iteration + 1) * thickness to avoid overlap at 0
            add_one = nodes.new("ShaderNodeMath")
            add_one.operation = 'ADD'
            links.new(repeat_in.outputs["Iteration"], add_one.inputs[0])
            add_one.inputs[1].default_value = 1.0

            math = nodes.new("ShaderNodeMath")
            math.operation = 'MULTIPLY'
            links.new(add_one.outputs[0], math.inputs[0])
            links.new(gin.outputs["Thickness"], math.inputs[1])

            # Taper based on UV channel
            named_attr = nodes.new("GeometryNodeInputNamedAttribute")
            named_attr.data_type = 'FLOAT_VECTOR'
            named_attr.inputs[0].default_value = "UVMap"

            separate_xyz = nodes.new("ShaderNodeSeparateXYZ")
            links.new(named_attr.outputs["Attribute"], separate_xyz.inputs[0])

            taper_axis = context.scene.shell_taper_axis
            taper_invert = context.scene.shell_taper_invert

            uv_value_output = "Y" if taper_axis == 'Y' else "X"
            uv_value = separate_xyz.outputs[uv_value_output]

            if taper_invert:
                taper = nodes.new("ShaderNodeClamp")
                links.new(uv_value, taper.inputs[0])
                taper.inputs[1].default_value = 0.0
                taper.inputs[2].default_value = 1.0
                taper_out = taper.outputs[0]
            else:
                subtract = nodes.new("ShaderNodeMath")
                subtract.operation = 'SUBTRACT'
                subtract.inputs[0].default_value = 1.0
                links.new(uv_value, subtract.inputs[1])
                
                taper = nodes.new("ShaderNodeClamp")
                links.new(subtract.outputs[0], taper.inputs[0])
                taper.inputs[1].default_value = 0.0
                taper.inputs[2].default_value = 1.0
                taper_out = taper.outputs[0]

            # Multiply thickness by taper
            math_mult = nodes.new("ShaderNodeMath")
            math_mult.operation = 'MULTIPLY'
            links.new(math.outputs[0], math_mult.inputs[0])
            links.new(taper_out, math_mult.inputs[1])

            vec = nodes.new("ShaderNodeVectorMath")
            vec.operation = 'SCALE'
            links.new(nodes.new("GeometryNodeInputNormal").outputs[0], vec.inputs[0])
            links.new(math_mult.outputs[0], vec.inputs[3])

            setpos = nodes.new("GeometryNodeSetPosition")
            links.new(repeat_in.outputs["Src"], setpos.inputs["Geometry"])
            links.new(vec.outputs[0], setpos.inputs["Offset"])

            # Set material index
            int_start = nodes.new("FunctionNodeInputInt")
            int_start.integer = slot_starts[idx]

            add_index = nodes.new("ShaderNodeMath")
            add_index.operation = 'ADD'
            links.new(repeat_in.outputs["Iteration"], add_index.inputs[0])
            links.new(int_start.outputs[0], add_index.inputs[1])

            set_index = nodes.new("GeometryNodeSetMaterialIndex")
            links.new(setpos.outputs["Geometry"], set_index.inputs["Geometry"])
            links.new(add_index.outputs[0], set_index.inputs["Material Index"])

            join = nodes.new("GeometryNodeJoinGeometry")
            links.new(repeat_in.outputs["Accum"], join.inputs["Geometry"])
            links.new(set_index.outputs["Geometry"], join.inputs["Geometry"])

            links.new(join.outputs["Geometry"], repeat_out.inputs["Accum"])
            links.new(repeat_in.outputs["Src"], repeat_out.inputs["Src"])

            links.new(repeat_out.outputs["Accum"], join_final.inputs["Geometry"])

        links.new(join_final.outputs["Geometry"], gout.inputs["Geometry"])

        if "Shell Fur" not in obj.modifiers:
            mod = obj.modifiers.new("Shell Fur", 'NODES')
            mod.node_group = gn

        self.report({'INFO'}, "Shell texturing with MToon materials created!")
        return {'FINISHED'}


# ------------------------------------------------------------
# Operator for turning off outline
# ------------------------------------------------------------

class TurnOffOutlineOperator(bpy.types.Operator):
    bl_idname = "object.turn_off_outline"
    bl_label = "Turn Off Outline"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "Select a mesh object.")
            return {'CANCELLED'}

        # Get checked materials only
        checked_materials = [
            item.material for item in obj.vrm_shell_materials
            if item.use_shell and item.material
        ]

        if not checked_materials:
            self.report({'ERROR'}, "No materials enabled.")
            return {'CANCELLED'}

        # Turn off outlines only for the checked materials (not shell materials)
        count = 0
        for mat in checked_materials:
            try:
                mat.vrm_addon_extension.mtoon1.extensions.vrmc_materials_mtoon.outline_width_mode = 'none'
                mat.vrm_addon_extension.mtoon1.extensions.vrmc_materials_mtoon.outline_width_factor = 0.0
                count += 1
            except:
                pass

        self.report({'INFO'}, f"Outlines turned off for {count} material(s)!")
        return {'FINISHED'}


# ------------------------------------------------------------
# UI
# ------------------------------------------------------------

class ShellTexturingPanel(bpy.types.Panel):
    bl_label = "VRM Hair Shell Texturing (MToon)"
    bl_idname = "OBJECT_PT_vrm_shell_mtoon"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "VRM"

    def draw(self, context):
        layout = self.layout
        obj = context.active_object

        if not obj or obj.type != 'MESH':
            layout.label(text="Select a mesh")
            return

        layout.prop(context.scene, "shell_layers")
        layout.prop(context.scene, "shell_taper_axis")
        layout.prop(context.scene, "shell_taper_invert")
        layout.prop(context.scene, "shell_texture_pattern")

        box = layout.box()
        box.label(text="Shell Materials")
        
        # Add refresh button
        box.operator("object.sync_shell_materials", icon='FILE_REFRESH')

        for item in obj.vrm_shell_materials:
            if item.material:
                row = box.row()
                row.prop(item, "use_shell", text="")
                row.label(text=item.material.name)

        layout.operator("object.add_shell_texturing", icon='MOD_PARTICLES')
        layout.operator("object.turn_off_outline", icon='CANCEL')


# ------------------------------------------------------------
# Registration
# ------------------------------------------------------------

classes = (
    VRMShellMaterialItem,
    SyncMaterialsOperator,
    ShellTexturingOperator,
    TurnOffOutlineOperator,
    ShellTexturingPanel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Object.vrm_shell_materials = bpy.props.CollectionProperty(
        type=VRMShellMaterialItem
    )

    bpy.types.Scene.shell_layers = bpy.props.IntProperty(
        name="Layers", default=10, min=1, max=64
    )

    bpy.types.Scene.shell_taper_axis = bpy.props.EnumProperty(
        name="Taper Axis",
        items=(('Y', "V (Y)", "Use UV V coordinate for tapering"), ('X', "U (X)", "Use UV U coordinate for tapering")),
        default='X'
    )

    bpy.types.Scene.shell_taper_invert = bpy.props.BoolProperty(
        name="Invert Taper Direction",
        default=False
    )

    bpy.types.Scene.shell_texture_pattern = bpy.props.EnumProperty(
        name="Texture Pattern",
        items=(('RANDOM', "Random", "Random pixel deletion"), ('VERTICAL', "Vertical", "Interspaced vertical lines semi-randomly")),
        default='RANDOM'
    )

def unregister():
    del bpy.types.Object.vrm_shell_materials
    del bpy.types.Scene.shell_layers
    del bpy.types.Scene.shell_taper_axis
    del bpy.types.Scene.shell_taper_invert
    del bpy.types.Scene.shell_texture_pattern

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()