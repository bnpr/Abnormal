import bpy
import mathutils
import bgl
import gpu
import random
from gpu_extras.batch import batch_for_shader
from .functions_general import *


class ABNPoints:
    def __init__(self, shader, mat):
        self.points = []
        self.shader = shader
        self.matrix = mat

        self.po_color = (0.1, 0.1, 0, 1)
        self.po_sel_color = (0.8, 0.8, 0.1, 1)
        self.po_act_color = (1, 1, 1, 1)
        self.line_color = (0.5, 0.3, 0.5, 1)
        self.line_sel_color = (0.9, 0.3, 0.9, 1)
        self.line_act_color = (0.9, 0.9, 0.9, 1)

    
    def add_point(self, pos, norm, loop_norms, loop_inds):
        po = ABNPoint(pos, norm, loop_norms, loop_inds, len(self.points), True)

        self.points.append(po)
        return
    
    def add_empty_point(self, pos, norm):
        po = ABNPoint(pos, norm, [], [], len(self.points), False)

        self.points.append(po)
        return
    
    def get_visible(self):
        vis_pos = [po.index for po in self.points if po.valid and po.hide == False]
        return vis_pos

    def get_selected(self):
        sel_pos = [po.index for po in self.points if po.select and po.valid and po.hide == False]
        return sel_pos
    
    def get_selected_cos(self):
        sel_pos = [po.index for po in self.points if po.select and po.valid and po.hide == False]
        sel_cos = [po.co for po in self.points if po.index in sel_pos]

        return sel_cos

    def get_unselected(self):
        sel_pos = [po.index for po in self.points if po.select == False and po.valid and po.hide == False]
        return sel_pos
    
    def get_current_normals(self):
        cache_norms = []
        for po in self.points:
            norms = []
            for l in po.loop_normals:
                norms.append(l)
            cache_norms.append(norms)
        return cache_norms

    def get_world_norm(self, norm, world_co):
        local_co = self.matrix.inverted() @ world_co

        norm_co = local_co+norm

        world_norm = self.matrix @ norm_co

        new_norm = (world_norm - world_co).normalized()

        del(local_co)
        del(norm_co)
        del(world_norm)
        return new_norm

    def update(self, norm_scale, act_po, sel_limit, sel_scale):
        points = []
        sel_points = []
        act_points = []
        lines = []
        sel_lines = []
        act_lines = []

        offset_co = None
        line_co = None
        for po in self.points:
            if po.hide == False and po.valid:
                offset_co = po.co
                fac = 1.0
                if po.index == act_po:
                    act_points.append(offset_co)
                    for l_norm in po.loop_normals:
                        line_co =  offset_co + self.get_world_norm(l_norm, offset_co)*norm_scale*fac

                        act_lines.append(offset_co)
                        act_lines.append(line_co)
                
                elif po.select:
                    if sel_scale:
                        fac = 0.666
                    sel_points.append(offset_co)
                    for l_norm in po.loop_normals:
                        line_co =  offset_co + self.get_world_norm(l_norm, offset_co)*norm_scale*fac

                        sel_lines.append(offset_co)
                        sel_lines.append(line_co)
                else:
                    points.append(offset_co)
                
                    if sel_limit == False or po.select:
                        if sel_scale:
                            fac = 0.333
                        for l_norm in po.loop_normals:
                            line_co =  offset_co + self.get_world_norm(l_norm, offset_co)*norm_scale*fac

                            lines.append(offset_co)
                            lines.append(line_co)
                

        self.batch_po = batch_for_shader(self.shader, 'POINTS', {"pos": points}) 
        self.batch_sel_po = batch_for_shader(self.shader, 'POINTS', {"pos": sel_points}) 
        self.batch_act_po = batch_for_shader(self.shader, 'POINTS', {"pos": act_points}) 
        self.batch_normal = batch_for_shader(self.shader, 'LINES', {"pos": lines}) 
        self.batch_sel_normal = batch_for_shader(self.shader, 'LINES', {"pos": sel_lines}) 
        self.batch_act_normal = batch_for_shader(self.shader, 'LINES', {"pos": act_lines}) 
        
        del(offset_co)
        del(line_co)
        return
    

    def draw_po(self, active, depth, b_scale, po_scale):
        size = 5*po_scale
        render_color = [self.po_color[0]*b_scale, self.po_color[1]*b_scale, self.po_color[2]*b_scale, self.po_color[3]]
        
        bgl.glEnable(bgl.GL_BLEND)
        if depth == False:
            bgl.glEnable(bgl.GL_DEPTH_TEST)
        bgl.glPointSize(size)
        self.shader.bind()
        self.shader.uniform_float("color", render_color)
        self.batch_po.draw(self.shader)
        bgl.glDisable(bgl.GL_BLEND)
        if depth == False:
            bgl.glDisable(bgl.GL_DEPTH_TEST)
    
    def draw_sel_po(self, active, depth, b_scale, po_scale):
        size = 7*po_scale
        render_color = [self.po_sel_color[0]*b_scale, self.po_sel_color[1]*b_scale, self.po_sel_color[2]*b_scale, self.po_sel_color[3]]
        
        bgl.glEnable(bgl.GL_BLEND)
        if depth == False:
            bgl.glEnable(bgl.GL_DEPTH_TEST)
        bgl.glPointSize(size)
        self.shader.bind()
        self.shader.uniform_float("color", render_color)
        self.batch_sel_po.draw(self.shader)
        bgl.glDisable(bgl.GL_BLEND)
        if depth == False:
            bgl.glDisable(bgl.GL_DEPTH_TEST)
    
    def draw_act_po(self, active, depth, b_scale, po_scale):
        size = 9*po_scale
        render_color = [self.po_act_color[0]*b_scale, self.po_act_color[1]*b_scale, self.po_act_color[2]*b_scale, self.po_act_color[3]]
        
        bgl.glEnable(bgl.GL_BLEND)
        if depth == False:
            bgl.glEnable(bgl.GL_DEPTH_TEST)
        bgl.glPointSize(size)
        self.shader.bind()
        self.shader.uniform_float("color", render_color)
        self.batch_act_po.draw(self.shader)
        bgl.glDisable(bgl.GL_BLEND)
        if depth == False:
            bgl.glDisable(bgl.GL_DEPTH_TEST)
    
    def draw_line(self, depth, b_scale):
        render_color = [self.line_color[0]*b_scale, self.line_color[1]*b_scale, self.line_color[2]*b_scale, self.line_color[3]]
        
        bgl.glEnable(bgl.GL_BLEND)
        if depth == False:
            bgl.glEnable(bgl.GL_DEPTH_TEST)
        bgl.glLineWidth(1)
        self.shader.bind()
        self.shader.uniform_float("color", render_color)
        self.batch_normal.draw(self.shader)
        bgl.glDisable(bgl.GL_BLEND)
        if depth == False:
            bgl.glDisable(bgl.GL_DEPTH_TEST)
    
    def draw_sel_line(self, depth, b_scale):
        render_color = [self.line_sel_color[0]*b_scale, self.line_sel_color[1]*b_scale, self.line_sel_color[2]*b_scale, self.line_sel_color[3]]
        
        bgl.glEnable(bgl.GL_BLEND)
        if depth == False:
            bgl.glEnable(bgl.GL_DEPTH_TEST)
        bgl.glLineWidth(1)
        self.shader.bind()
        self.shader.uniform_float("color", render_color)
        self.batch_sel_normal.draw(self.shader)
        bgl.glDisable(bgl.GL_BLEND)
        if depth == False:
            bgl.glDisable(bgl.GL_DEPTH_TEST)
    
    def draw_act_line(self, depth, b_scale):
        render_color = [self.line_act_color[0]*b_scale, self.line_act_color[1]*b_scale, self.line_act_color[2]*b_scale, self.line_act_color[3]]
        
        bgl.glEnable(bgl.GL_BLEND)
        if depth == False:
            bgl.glEnable(bgl.GL_DEPTH_TEST)
        bgl.glLineWidth(2)
        self.shader.bind()
        self.shader.uniform_float("color", render_color)
        self.batch_act_normal.draw(self.shader)
        bgl.glDisable(bgl.GL_BLEND)
        if depth == False:
            bgl.glDisable(bgl.GL_DEPTH_TEST)
    
    
    def __str__(self, ):
        return 'Object Vertex Points'

class ABNPoint:
    def __init__(self, position, norm, loop_norms, loop_inds, index, validity):
        self.co = position
        self.normal = norm
        self.loop_normals = loop_norms
        self.loop_inds = loop_inds
        self.select = False
        self.hide = False
        self.index = index
        self.valid = validity
    
    def __str__(self, ):
        return 'Object Vertex Point'

class ABNLoop:
    def __init__(self, norm, index):
        self.normal = norm
        self.select = False
        self.index = index
    
    def __str__(self, ):
        return 'Object Vertex Loop'