#!/usr/bin/env python3
"""
FinOps Best Practices PowerPoint Generator

Creates a PowerPoint slide with click-triggered animations that highlight
each of the four FinOps sections: Visibility, Optimize, Collaborate, Automate.

Each click reveals the next section in the cycle.
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from lxml import etree


def create_finops_slide():
    """Create the FinOps Best Practices slide with animations."""

    prs = Presentation()
    prs.slide_width = Inches(13.333)  # 16:9 aspect ratio
    prs.slide_height = Inches(7.5)

    # Add a blank slide
    blank_layout = prs.slide_layouts[6]  # Blank layout
    slide = prs.slides.add_slide(blank_layout)

    # Colors
    blue_color = RGBColor(0, 120, 212)  # Primary blue
    dark_color = RGBColor(0, 0, 0)      # Black for title

    # === LEFT SIDE CONTENT ===

    # Title: "FinOps Best Practices"
    title_box = slide.shapes.add_textbox(Inches(0.5), Inches(0.4), Inches(5), Inches(0.8))
    title_frame = title_box.text_frame
    title_para = title_frame.paragraphs[0]
    title_para.text = "FinOps Best Practices"
    title_para.font.size = Pt(40)
    title_para.font.bold = True
    title_para.font.color.rgb = dark_color

    # Subtitle
    subtitle_box = slide.shapes.add_textbox(Inches(0.5), Inches(1.1), Inches(6), Inches(0.5))
    subtitle_frame = subtitle_box.text_frame
    subtitle_para = subtitle_frame.paragraphs[0]
    subtitle_para.text = "Industry Best Practices Powered by CloudHealth"
    subtitle_para.font.size = Pt(18)
    subtitle_para.font.color.rgb = blue_color

    # Quote text
    quote_box = slide.shapes.add_textbox(Inches(0.5), Inches(2.0), Inches(5.5), Inches(2.5))
    quote_frame = quote_box.text_frame
    quote_frame.word_wrap = True

    # First paragraph - quote
    p1 = quote_frame.paragraphs[0]
    run1 = p1.add_run()
    run1.text = '"'
    run1.font.size = Pt(16)

    run2 = p1.add_run()
    run2.text = "FinOps"
    run2.font.size = Pt(16)
    run2.font.color.rgb = blue_color

    run3 = p1.add_run()
    run3.text = " isn't just about saving money - it's about "
    run3.font.size = Pt(16)

    run4 = p1.add_run()
    run4.text = "maximizing business value through disciplined, data-driven decision-making."
    run4.font.size = Pt(16)
    run4.font.color.rgb = blue_color

    # Second paragraph - tools description
    p2 = quote_frame.add_paragraph()
    p2.space_before = Pt(20)
    run5 = p2.add_run()
    run5.text = "Tools like "
    run5.font.size = Pt(16)

    run6 = p2.add_run()
    run6.text = "CloudHealth"
    run6.font.size = Pt(16)
    run6.font.color.rgb = blue_color

    run7 = p2.add_run()
    run7.text = ' transform best practices into operational reality."'
    run7.font.size = Pt(16)

    # Attribution
    p3 = quote_frame.add_paragraph()
    p3.space_before = Pt(20)
    run8 = p3.add_run()
    run8.text = "- FinOps Foundation, 2024 State of FinOps Report"
    run8.font.size = Pt(14)
    run8.font.italic = True
    run8.font.color.rgb = blue_color

    # === RIGHT SIDE - CYCLE DIAGRAM ===

    # Center point for the cycle
    center_x = Inches(9.5)
    center_y = Inches(4.0)
    radius = Inches(1.8)

    # Section positions (clockwise from top)
    sections = [
        {"name": "Visibility", "pos": (center_x, center_y - radius), "icon": "eye"},
        {"name": "Optimize", "pos": (center_x + radius, center_y), "icon": "target"},
        {"name": "Collaborate", "pos": (center_x, center_y + radius), "icon": "people"},
        {"name": "Automate", "pos": (center_x - radius, center_y), "icon": "gear"},
    ]

    # Shape IDs for animation tracking
    shape_groups = []

    for i, section in enumerate(sections):
        x, y = section["pos"]

        # Cloud shape (approximated with rounded rectangle)
        cloud = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            x - Inches(0.6),
            y - Inches(0.5),
            Inches(1.2),
            Inches(1.0)
        )
        cloud.fill.solid()
        cloud.fill.fore_color.rgb = RGBColor(255, 255, 255)
        cloud.line.color.rgb = blue_color
        cloud.line.width = Pt(2)

        # Label below the cloud
        label = slide.shapes.add_textbox(
            x - Inches(0.7),
            y + Inches(0.6),
            Inches(1.4),
            Inches(0.4)
        )
        label_frame = label.text_frame
        label_para = label_frame.paragraphs[0]
        label_para.text = section["name"]
        label_para.font.size = Pt(14)
        label_para.font.bold = True
        label_para.font.color.rgb = dark_color
        label_para.alignment = PP_ALIGN.CENTER

        # Store shape IDs for animation
        shape_groups.append({
            "cloud_id": cloud.shape_id,
            "label_id": label.shape_id,
            "name": section["name"]
        })

    # Add curved arrows between sections
    arrow_positions = [
        # Top to Right
        (center_x + Inches(0.7), center_y - radius + Inches(0.3), 45),
        # Right to Bottom
        (center_x + radius - Inches(0.3), center_y + Inches(0.7), 135),
        # Bottom to Left
        (center_x - Inches(0.7), center_y + radius - Inches(0.3), 225),
        # Left to Top
        (center_x - radius + Inches(0.3), center_y - Inches(0.7), 315),
    ]

    for x, y, rotation in arrow_positions:
        arrow = slide.shapes.add_shape(
            MSO_SHAPE.RIGHT_ARROW,
            x - Inches(0.3),
            y - Inches(0.15),
            Inches(0.6),
            Inches(0.3)
        )
        arrow.fill.solid()
        arrow.fill.fore_color.rgb = blue_color
        arrow.line.fill.background()
        arrow.rotation = rotation

    # Footer
    footer_box = slide.shapes.add_textbox(Inches(0.5), Inches(7.0), Inches(3), Inches(0.3))
    footer_frame = footer_box.text_frame
    footer_para = footer_frame.paragraphs[0]
    footer_para.text = "ARROW | CloudHealth"
    footer_para.font.size = Pt(12)
    footer_para.font.color.rgb = dark_color

    # Page number
    page_box = slide.shapes.add_textbox(Inches(12.5), Inches(7.0), Inches(0.5), Inches(0.3))
    page_frame = page_box.text_frame
    page_para = page_frame.paragraphs[0]
    page_para.text = "11"
    page_para.font.size = Pt(12)
    page_para.font.color.rgb = RGBColor(128, 128, 128)
    page_para.alignment = PP_ALIGN.RIGHT

    # Add animations
    add_click_animations(slide, shape_groups)

    return prs


def add_click_animations(slide, shape_groups):
    """
    Add click-triggered animations to highlight each section.

    Animation sequence:
    1. Click 1: Visibility section appears/highlights
    2. Click 2: Optimize section appears/highlights
    3. Click 3: Collaborate section appears/highlights
    4. Click 4: Automate section appears/highlights
    """

    # Get the slide's spTree element
    spTree = slide.shapes._spTree

    # Define namespaces
    nsmap_anim = {
        'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
        'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
        'p': 'http://schemas.openxmlformats.org/presentationml/2006/main'
    }

    # Create timing element for the slide
    timing_xml = create_timing_xml(shape_groups)

    # Parse and add to slide
    timing_element = etree.fromstring(timing_xml)

    # Find or create timing element in slide
    sld = slide._element
    existing_timing = sld.find('{http://schemas.openxmlformats.org/presentationml/2006/main}timing')
    if existing_timing is not None:
        sld.remove(existing_timing)

    sld.append(timing_element)


def create_timing_xml(shape_groups):
    """Create the XML for click-triggered animations."""

    # Build animation sequences for each section
    seq_children = ""

    for i, group in enumerate(shape_groups):
        click_num = i + 1
        cloud_id = group["cloud_id"]
        label_id = group["label_id"]

        # Each click triggers a fade-in and emphasis animation
        seq_children += f'''
        <p:seq concurrent="1" nextAc="seek" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
          <p:cTn id="{10 + i*20}" dur="indefinite" nodeType="mainSeq">
            <p:childTnLst>
              <p:par>
                <p:cTn id="{11 + i*20}" fill="hold">
                  <p:stCondLst>
                    <p:cond delay="indefinite"/>
                    <p:cond evt="onBegin" delay="0">
                      <p:tn val="{10 + i*20}"/>
                    </p:cond>
                  </p:stCondLst>
                  <p:childTnLst>
                    <p:par>
                      <p:cTn id="{12 + i*20}" fill="hold">
                        <p:stCondLst>
                          <p:cond delay="0"/>
                        </p:stCondLst>
                        <p:childTnLst>
                          <!-- Emphasis animation for cloud shape -->
                          <p:par>
                            <p:cTn id="{13 + i*20}" presetID="10" presetClass="emph" presetSubtype="0" fill="hold" nodeType="clickEffect">
                              <p:stCondLst>
                                <p:cond delay="0"/>
                              </p:stCondLst>
                              <p:childTnLst>
                                <p:animClr clrSpc="rgb" dir="cw">
                                  <p:cBhvr>
                                    <p:cTn id="{14 + i*20}" dur="500" fill="hold"/>
                                    <p:tgtEl>
                                      <p:spTgt spid="{cloud_id}"/>
                                    </p:tgtEl>
                                    <p:attrNameLst>
                                      <p:attrName>fillcolor</p:attrName>
                                    </p:attrNameLst>
                                  </p:cBhvr>
                                  <p:to>
                                    <a:srgbClr val="0078D4" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"/>
                                  </p:to>
                                </p:animClr>
                              </p:childTnLst>
                            </p:cTn>
                          </p:par>
                          <!-- Scale animation for emphasis -->
                          <p:par>
                            <p:cTn id="{15 + i*20}" presetID="6" presetClass="emph" presetSubtype="0" fill="hold" nodeType="withEffect">
                              <p:stCondLst>
                                <p:cond delay="0"/>
                              </p:stCondLst>
                              <p:childTnLst>
                                <p:animScale>
                                  <p:cBhvr>
                                    <p:cTn id="{16 + i*20}" dur="500" fill="hold"/>
                                    <p:tgtEl>
                                      <p:spTgt spid="{cloud_id}"/>
                                    </p:tgtEl>
                                  </p:cBhvr>
                                  <p:by x="110000" y="110000"/>
                                </p:animScale>
                              </p:childTnLst>
                            </p:cTn>
                          </p:par>
                          <!-- Bold text animation for label -->
                          <p:par>
                            <p:cTn id="{17 + i*20}" presetID="10" presetClass="emph" presetSubtype="0" fill="hold" nodeType="withEffect">
                              <p:stCondLst>
                                <p:cond delay="0"/>
                              </p:stCondLst>
                              <p:childTnLst>
                                <p:animClr clrSpc="rgb" dir="cw">
                                  <p:cBhvr>
                                    <p:cTn id="{18 + i*20}" dur="500" fill="hold"/>
                                    <p:tgtEl>
                                      <p:spTgt spid="{label_id}"/>
                                    </p:tgtEl>
                                    <p:attrNameLst>
                                      <p:attrName>style.color</p:attrName>
                                    </p:attrNameLst>
                                  </p:cBhvr>
                                  <p:to>
                                    <a:srgbClr val="0078D4" xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"/>
                                  </p:to>
                                </p:animClr>
                              </p:childTnLst>
                            </p:cTn>
                          </p:par>
                        </p:childTnLst>
                      </p:cTn>
                    </p:par>
                  </p:childTnLst>
                </p:cTn>
              </p:par>
            </p:childTnLst>
          </p:cTn>
          <p:prevCondLst>
            <p:cond evt="onPrev" delay="0">
              <p:tgtEl>
                <p:sldTgt/>
              </p:tgtEl>
            </p:cond>
          </p:prevCondLst>
          <p:nextCondLst>
            <p:cond evt="onNext" delay="0">
              <p:tgtEl>
                <p:sldTgt/>
              </p:tgtEl>
            </p:cond>
          </p:nextCondLst>
        </p:seq>'''

    timing_xml = f'''<p:timing xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
      <p:tnLst>
        <p:par>
          <p:cTn id="1" dur="indefinite" restart="never" nodeType="tmRoot">
            <p:childTnLst>
              {seq_children}
            </p:childTnLst>
          </p:cTn>
        </p:par>
      </p:tnLst>
    </p:timing>'''

    return timing_xml


def main():
    """Main function to generate the PowerPoint."""
    print("Creating FinOps Best Practices slide with animations...")

    prs = create_finops_slide()

    output_file = "finops_best_practices.pptx"
    prs.save(output_file)

    print(f"Successfully created: {output_file}")
    print("\nAnimation sequence:")
    print("  Click 1: Highlights 'Visibility' section")
    print("  Click 2: Highlights 'Optimize' section")
    print("  Click 3: Highlights 'Collaborate' section")
    print("  Click 4: Highlights 'Automate' section")
    print("\nOpen the file in PowerPoint and press F5 to start the slideshow.")


if __name__ == "__main__":
    main()
