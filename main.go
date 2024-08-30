package main

import (
	"fmt"
	"os"
	"os/exec"
	"runtime"

	"github.com/getlantern/systray"
)

func main() {
	onExit := func() {
		// 清理任务（如果有）
	}

	systray.Run(onReady, onExit)
}

func onReady() {
	// 设置托盘图标和提示文本
	systray.SetIcon(getIcon("favicon.ico")) // 替换为实际的图标路径
	systray.SetTitle("Simple App")
	systray.SetTooltip("Click to open the browser")

	// 添加菜单项
	mOpen := systray.AddMenuItem("Open Browser", "Open the web interface")
	mQuit := systray.AddMenuItem("Quit", "Quit the application")

	// 监听菜单项点击事件
	go func() {
		for {
			select {
			case <-mOpen.ClickedCh:
				openBrowser("http://localhost:8080") // 替换为实际的URL
			case <-mQuit.ClickedCh:
				systray.Quit()
				return
			}
		}
	}()

	fmt.Println("Tray application started")
}

// openBrowser 打开默认浏览器访问指定的 URL
func openBrowser(url string) {
	var cmd string
	var args []string

	switch runtime.GOOS {
	case "windows":
		cmd = "rundll32"
		args = []string{"url.dll,FileProtocolHandler", url}
	case "darwin":
		cmd = "open"
		args = []string{url}
	case "linux":
		cmd = "xdg-open"
		args = []string{url}
	default:
		fmt.Printf("unsupported platform")
		return
	}

	err := exec.Command(cmd, args...).Start()
	if err != nil {
		fmt.Printf("failed to open browser: %v\n", err)
	}
}

// getIcon 函数从文件或嵌入中加载图标（根据需要调整）
// 在 Windows 上使用 .ico 文件，在 macOS 和 Linux 上可以使用 .png 文件
func getIcon(s string) []byte {
	// 示例代码：读取图标文件
	iconData, err := os.ReadFile(s)
	if err != nil {
		fmt.Println("Error reading icon file:", err)
		return nil
	}
	return iconData
}
