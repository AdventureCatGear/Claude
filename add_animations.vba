' FinOps Slide Animation VBA Script
'
' This VBA macro adds click-triggered animations to highlight each of the four
' FinOps sections (Visibility, Optimize, Collaborate, Automate) in sequence.
'
' INSTRUCTIONS:
' 1. Open your PowerPoint presentation
' 2. Press Alt+F11 to open the VBA Editor
' 3. Insert > Module
' 4. Paste this code
' 5. Select the slide with your FinOps diagram
' 6. Run the macro: AddFinOpsAnimations
'
' PREREQUISITES:
' - Your slide must have shapes named: "Visibility", "Optimize", "Collaborate", "Automate"
' - Or modify the shape names in the arrays below to match your shapes

Sub AddFinOpsAnimations()
    Dim sld As Slide
    Dim shp As Shape
    Dim eff As Effect
    Dim seq As Sequence
    Dim i As Integer

    ' Section names in order of animation
    Dim sectionNames(1 To 4) As String
    sectionNames(1) = "Visibility"
    sectionNames(2) = "Optimize"
    sectionNames(3) = "Collaborate"
    sectionNames(4) = "Automate"

    ' Get the active slide
    On Error Resume Next
    Set sld = ActiveWindow.View.Slide
    On Error GoTo 0

    If sld Is Nothing Then
        MsgBox "Please select a slide first.", vbExclamation
        Exit Sub
    End If

    ' Get the main animation sequence
    Set seq = sld.TimeLine.MainSequence

    ' Clear existing animations (optional - comment out to preserve)
    ' Do While seq.Count > 0
    '     seq(1).Delete
    ' Loop

    ' Add animations for each section
    For i = 1 To 4
        ' Find the shape for this section
        Set shp = FindShapeByName(sld, sectionNames(i))

        If shp Is Nothing Then
            ' Try to find a group or shape containing the section name
            Set shp = FindShapeContainingText(sld, sectionNames(i))
        End If

        If Not shp Is Nothing Then
            ' Add emphasis animation (Grow/Shrink with color change)

            ' First effect: Color Pulse
            Set eff = seq.AddEffect(shp, msoAnimEffectChangeFillColor, _
                                    trigger:=msoAnimTriggerOnPageClick)
            With eff
                .Timing.Duration = 0.5
                .EffectParameters.Color2.RGB = RGB(0, 120, 212) ' Blue highlight
            End With

            ' Second effect: Grow (simultaneous with color)
            Set eff = seq.AddEffect(shp, msoAnimEffectGrowShrink, _
                                    trigger:=msoAnimTriggerWithPrevious)
            With eff
                .Timing.Duration = 0.5
                .EffectParameters.Size = 1.1 ' 110% size
            End With

            ' Third effect: Shrink back (after grow)
            Set eff = seq.AddEffect(shp, msoAnimEffectGrowShrink, _
                                    trigger:=msoAnimTriggerAfterPrevious)
            With eff
                .Timing.Duration = 0.3
                .EffectParameters.Size = 1.0 ' Back to 100%
            End With
        Else
            Debug.Print "Shape not found for: " & sectionNames(i)
        End If
    Next i

    MsgBox "Animations added successfully!" & vbCrLf & _
           "Click sequence: Visibility -> Optimize -> Collaborate -> Automate", vbInformation
End Sub

' Alternative approach: Add animations by shape selection
Sub AddAnimationsToSelectedShapes()
    Dim sld As Slide
    Dim shp As Shape
    Dim sel As Selection
    Dim eff As Effect
    Dim seq As Sequence
    Dim i As Integer

    Set sel = ActiveWindow.Selection

    If sel.Type <> ppSelectionShapes Then
        MsgBox "Please select the 4 shapes in order: Visibility, Optimize, Collaborate, Automate", vbExclamation
        Exit Sub
    End If

    Set sld = ActiveWindow.View.Slide
    Set seq = sld.TimeLine.MainSequence

    For i = 1 To sel.ShapeRange.Count
        Set shp = sel.ShapeRange(i)

        ' Add click-triggered emphasis
        Set eff = seq.AddEffect(shp, msoAnimEffectChangeFillColor, _
                                trigger:=msoAnimTriggerOnPageClick)
        With eff
            .Timing.Duration = 0.5
            .EffectParameters.Color2.RGB = RGB(0, 120, 212)
        End With

        ' Add scale animation
        Set eff = seq.AddEffect(shp, msoAnimEffectGrowShrink, _
                                trigger:=msoAnimTriggerWithPrevious)
        With eff
            .Timing.Duration = 0.5
            .EffectParameters.Size = 1.15
        End With

        ' Shrink back
        Set eff = seq.AddEffect(shp, msoAnimEffectGrowShrink, _
                                trigger:=msoAnimTriggerAfterPrevious)
        With eff
            .Timing.Duration = 0.3
            .EffectParameters.Size = 1.0
        End With
    Next i

    MsgBox "Animations added to " & sel.ShapeRange.Count & " shapes!", vbInformation
End Sub

' Simple highlight animation approach
Sub AddSimpleHighlightAnimations()
    Dim sld As Slide
    Dim shp As Shape
    Dim eff As Effect
    Dim seq As Sequence
    Dim shapeIndex As Integer

    Set sld = ActiveWindow.View.Slide
    Set seq = sld.TimeLine.MainSequence

    ' Instructions
    MsgBox "This will add Appear animations to all shapes on the slide." & vbCrLf & _
           "Shapes will appear in order when you click.", vbInformation

    shapeIndex = 0
    For Each shp In sld.Shapes
        ' Skip title placeholders
        If shp.Type = msoPlaceholder Then GoTo NextShape

        ' Add fade in animation
        Set eff = seq.AddEffect(shp, msoAnimEffectFade, _
                                trigger:=msoAnimTriggerOnPageClick)
        eff.Timing.Duration = 0.5

        shapeIndex = shapeIndex + 1
NextShape:
    Next shp

    MsgBox shapeIndex & " shapes will now appear on click.", vbInformation
End Sub

' Helper function to find shape by name
Private Function FindShapeByName(sld As Slide, shapeName As String) As Shape
    Dim shp As Shape

    For Each shp In sld.Shapes
        If InStr(1, shp.Name, shapeName, vbTextCompare) > 0 Then
            Set FindShapeByName = shp
            Exit Function
        End If
    Next shp

    Set FindShapeByName = Nothing
End Function

' Helper function to find shape containing text
Private Function FindShapeContainingText(sld As Slide, searchText As String) As Shape
    Dim shp As Shape

    For Each shp In sld.Shapes
        If shp.HasTextFrame Then
            If shp.TextFrame.HasText Then
                If InStr(1, shp.TextFrame.TextRange.Text, searchText, vbTextCompare) > 0 Then
                    Set FindShapeContainingText = shp
                    Exit Function
                End If
            End If
        End If

        ' Check grouped shapes
        If shp.Type = msoGroup Then
            Dim grpShp As Shape
            For Each grpShp In shp.GroupItems
                If grpShp.HasTextFrame Then
                    If grpShp.TextFrame.HasText Then
                        If InStr(1, grpShp.TextFrame.TextRange.Text, searchText, vbTextCompare) > 0 Then
                            Set FindShapeContainingText = shp
                            Exit Function
                        End If
                    End If
                End If
            Next grpShp
        End If
    Next shp

    Set FindShapeContainingText = Nothing
End Function
