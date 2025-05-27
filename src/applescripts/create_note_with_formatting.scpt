on run argv
    -- 参数：标题、内容、文件夹
    set noteTitle to item 1 of argv
    set noteContent to item 2 of argv
    set folderName to item 3 of argv
    
    tell application "Notes"
        activate
        
        -- 确定目标文件夹
        if folderName is not "" then
            try
                set targetFolder to folder folderName
            on error
                -- 如果文件夹不存在，创建它
                set targetFolder to make new folder with properties {name:folderName}
            end try
        else
            set targetFolder to default account's default folder
        end if
        
        -- 创建新笔记
        set newNote to make new note at targetFolder
        
        -- 设置标题
        if noteTitle is not "" then
            set name of newNote to noteTitle
        end if
        
        -- 等待笔记创建完成
        delay 0.5
        
        -- 激活笔记编辑
        tell application "System Events"
            -- 确保Notes是前台应用
            tell process "Notes"
                set frontmost to true
                delay 0.3
                
                -- 清空笔记内容（如果有默认内容）
                key code 0 using command down -- Cmd+A 全选
                delay 0.1
                key code 51 -- Delete
                delay 0.1
                
                -- 解析并输入格式化内容
                my processFormattedContent(noteContent)
            end tell
        end tell
        
        return "Note created successfully with rich formatting."
    end tell
end run

on processFormattedContent(content)
    -- 将内容按行分割处理
    set contentLines to paragraphs of content
    
    repeat with i from 1 to count of contentLines
        set currentLine to item i of contentLines
        
        if currentLine is not "" then
            -- 检测并应用格式
            if currentLine starts with "# " then
                -- 一级标题
                my insertTitle(text 3 thru -1 of currentLine)
            else if currentLine starts with "## " then
                -- 二级标题  
                my insertHeading(text 4 thru -1 of currentLine)
            else if currentLine starts with "### " then
                -- 三级标题
                my insertSubheading(text 5 thru -1 of currentLine)
            else if currentLine starts with "- " or currentLine starts with "• " then
                -- 列表项
                my insertListItem(text 3 thru -1 of currentLine)
            else if currentLine starts with "```" then
                -- 代码块开始/结束 - 跳过
            else if currentLine contains "    " and (currentLine does not start with " ") then
                -- 可能是代码行
                my insertMonospacedText(currentLine)
            else
                -- 普通段落
                my insertParagraph(currentLine)
            end if
        else
            -- 空行 - 添加段落间距
            my insertParagraphBreak()
        end if
    end repeat
end processFormattedContent

on insertTitle(titleText)
    tell application "System Events"
        tell process "Notes"
            -- 输入文本
            keystroke titleText
            delay 0.1
            
            -- 选中刚输入的文本
            key code 123 using {shift down, command down} -- Shift+Cmd+Left 选择整行
            delay 0.1
            
            -- 应用标题格式 (Cmd+Shift+T)
            key code 17 using {command down, shift down}
            delay 0.1
            
            -- 移到行尾并添加换行
            key code 124 using command down -- Cmd+Right
            keystroke return
            keystroke return -- 额外的换行增加间距
        end tell
    end tell
end insertTitle

on insertHeading(headingText)
    tell application "System Events"
        tell process "Notes"
            keystroke headingText
            delay 0.1
            
            -- 选中文本并应用标题格式
            key code 123 using {shift down, command down}
            delay 0.1
            
            -- 应用标题格式 (Cmd+Shift+H)
            key code 4 using {command down, shift down}
            delay 0.1
            
            key code 124 using command down
            keystroke return
            keystroke return
        end tell
    end tell
end insertHeading

on insertSubheading(subheadingText)
    tell application "System Events"
        tell process "Notes"
            keystroke subheadingText
            delay 0.1
            
            key code 123 using {shift down, command down}
            delay 0.1
            
            -- 应用子标题格式 (Cmd+Shift+J)
            key code 38 using {command down, shift down}
            delay 0.1
            
            key code 124 using command down
            keystroke return
            keystroke return
        end tell
    end tell
end insertSubheading

on insertListItem(itemText)
    tell application "System Events"
        tell process "Notes"
            keystroke itemText
            delay 0.1
            
            key code 123 using {shift down, command down}
            delay 0.1
            
            -- 应用项目符号列表格式 (Cmd+Shift+7)
            key code 26 using {command down, shift down}
            delay 0.1
            
            key code 124 using command down
            keystroke return
        end tell
    end tell
end insertListItem

on insertMonospacedText(codeText)
    tell application "System Events"
        tell process "Notes"
            keystroke codeText
            delay 0.1
            
            key code 123 using {shift down, command down}
            delay 0.1
            
            -- 应用等宽字体格式 (Cmd+Shift+M)
            key code 46 using {command down, shift down}
            delay 0.1
            
            key code 124 using command down
            keystroke return
            keystroke return
        end tell
    end tell
end insertMonospacedText

on insertParagraph(paragraphText)
    tell application "System Events"
        tell process "Notes"
            keystroke paragraphText
            keystroke return
            keystroke return -- 额外换行增加段落间距
        end tell
    end tell
end insertParagraph

on insertParagraphBreak()
    tell application "System Events"
        tell process "Notes"
            keystroke return
        end tell
    end tell
end insertParagraphBreak 