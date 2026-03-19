import { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import { FileDown, Loader2, Sparkles, XCircle, History, Trash2, Clock, Send, Edit3, LayoutList } from 'lucide-react';
import { Preview } from './components/Preview';
import './App.css';

interface SlideItem {
  title: string;
  description: string;
}

interface Slide {
  page_title: string;
  subtitle?: string;
  content: SlideItem[];
  layout_type: string;
  image_description?: string;
}

interface PPTContent {
  title: string;
  subtitle?: string;
  theme_color: string;
  accent_color: string;
  bg_style: string;
  slides: Slide[];
}

interface HistoryItem {
  id: string;
  title: string;
  content: PPTContent;
  pptx_filename: string;
  html_filename: string;
  timestamp: string;
}

function App() {
  const [topic, setTopic] = useState('');
  const [polishedTopic, setPolishedTopic] = useState('');
  const [isPolished, setIsPolished] = useState(false);
  const [apiKey, setApiKey] = useState('');
  const [provider, setProvider] = useState('openai'); // Default provider
  const [loading, setLoading] = useState(false);
  const [polishing, setPolishing] = useState(false);
  const [generatingFile, setGeneratingFile] = useState(false);
  const [generatingHtml, setGeneratingHtml] = useState(false);
  const [pptContent, setPptContent] = useState<PPTContent | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [viewMode, setViewMode] = useState<'input' | 'outline' | 'preview'>('input');
  const [modifyInstruction, setModifyInstruction] = useState('');
  const [modifying, setModifying] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Load history on mount
  useEffect(() => {
    fetchHistory();
  }, []);

  const fetchHistory = async () => {
    try {
      const response = await axios.get('http://127.0.0.1:8001/history');
      setHistory(response.data);
    } catch (err) {
      console.error('Failed to fetch history:', err);
    }
  };

  const deleteHistoryItem = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    try {
      await axios.delete(`http://127.0.0.1:8001/history/${id}`);
      setHistory(history.filter(item => item.id !== id));
    } catch (err) {
      console.error('Failed to delete history item:', err);
    }
  };

  const handleSelectHistory = (item: HistoryItem) => {
    setPptContent(item.content);
    setTopic(item.title);
    setIsPolished(false);
    setShowHistory(false);
    setViewMode('preview');
    // Scroll to preview
    setTimeout(() => {
      window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
    }, 100);
  };

  const handlePolish = async () => {
    if (!topic) return;
    console.log('--- Start Polishing ---');
    console.log('Request URL: http://127.0.0.1:8001/polish');
    console.log('Payload:', { topic, provider, api_key: apiKey ? '***' : 'null' });
    
    setPolishing(true);
    setError(null);
    try {
      const response = await axios.post('http://127.0.0.1:8001/polish', {
        topic,
        provider,
        api_key: apiKey || null,
      }, {
        timeout: 30000 // 30 seconds timeout
      });
      console.log('Polish Response:', response.data);
      setPolishedTopic(response.data.polished_topic);
      setIsPolished(true);
    } catch (err: any) {
      console.error('Polish Error:', err);
      setError(err.response?.data?.detail || err.message || '润色主题时出错');
    } finally {
      setPolishing(false);
    }
  };

  const handleGenerate = async () => {
    const finalTopic = isPolished ? polishedTopic : topic;
    if (!finalTopic) return;
    
    setLoading(true);
    setError(null);
    setPptContent(null);

    // Create a new AbortController for this request
    const controller = new AbortController();
    abortControllerRef.current = controller;

    console.log('--- Start Generation ---');
    console.log('Request URL: http://127.0.0.1:8001/generate');
    console.log('Payload:', { topic: finalTopic, provider, api_key: apiKey ? '***' : 'null' });

    try {
      const response = await axios.post<PPTContent>('http://127.0.0.1:8001/generate', {
        topic: finalTopic,
        provider,
        api_key: apiKey || null,
      }, {
        signal: controller.signal,
        timeout: 120000 // 60 seconds timeout
      });
      
      console.log('Response received:', response.data);
      if (response.data && Array.isArray(response.data.slides)) {
        setPptContent(response.data);
        setViewMode('outline');
        fetchHistory(); // Refresh history list
      } else {
        throw new Error('返回的数据格式不正确');
      }
    } catch (err: any) {
      if (axios.isCancel(err)) {
        console.log('Request canceled');
        setError('已取消生成');
      } else {
        console.error(err);
        const detail = err.response?.data?.detail;
        const message = typeof detail === 'string' ? detail : (err.message || '生成 PPT 内容时出错');
        setError(message);
      }
    } finally {
      setLoading(false);
      abortControllerRef.current = null;
    }
  };

  const handleCancel = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  };

  const handleDownload = async () => {
    if (!pptContent) return;

    setGeneratingFile(true);
    setError(null);

    try {
      const response = await axios.post('http://127.0.0.1:8001/download', pptContent);
      const filename = response.data.filename;
      const downloadUrl = `http://127.0.0.1:8001/get-file/${filename}?mode=download`;
      
      // Trigger download
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || err.message || 'Error downloading PPTX');
    } finally {
      setGeneratingFile(false);
    }
  };

  const handleDownloadHtml = async () => {
    if (!pptContent) return;

    setGeneratingHtml(true);
    setError(null);

    try {
      const response = await axios.post('http://127.0.0.1:8001/download-html', pptContent);
      const filename = response.data.filename;
      const downloadUrl = `http://127.0.0.1:8001/get-file/${filename}?mode=download`;
      
      // Trigger download
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || err.message || 'Error downloading HTML');
    } finally {
      setGeneratingHtml(false);
    }
  };

  const handlePreviewHtml = async () => {
    if (!pptContent) return;
    setGeneratingHtml(true);
    try {
      const response = await axios.post('http://127.0.0.1:8001/download-html', pptContent);
      const previewUrl = `http://127.0.0.1:8001${response.data.download_url}?mode=preview`;
      window.open(previewUrl, '_blank');
    } catch (err: any) {
      setError('无法打开预览');
    } finally {
      setGeneratingHtml(false);
    }
  };

  const handleModifyOutline = async () => {
    if (!modifyInstruction || !pptContent) return;
    console.log('--- Start Modifying Outline ---');
    console.log('Request URL: http://127.0.0.1:8001/modify-outline');
    console.log('Payload size:', JSON.stringify(pptContent).length);

    setModifying(true);
    setError(null);
    try {
      const response = await axios.post<PPTContent>('http://127.0.0.1:8001/modify-outline', {
        content: pptContent,
        instruction: modifyInstruction,
        provider,
        api_key: apiKey || null,
      }, {
        timeout: 60000 // 60 seconds timeout
      });
      console.log('Modify Response:', response.data);
      setPptContent(response.data);
      setModifyInstruction('');
      // Note: We don't fetchHistory here to avoid cluttering history with every tiny edit, 
      // but you could add a "Save" button later.
    } catch (err: any) {
      console.error('Modify Error:', err);
      setError(err.response?.data?.detail || err.message || '修改大纲时出错');
    } finally {
      setModifying(false);
    }
  };

  const handleSlideTitleChange = (index: number, newTitle: string) => {
    if (!pptContent) return;
    const newSlides = [...pptContent.slides];
    newSlides[index].page_title = newTitle;
    setPptContent({ ...pptContent, slides: newSlides });
  };

  const handleSlideItemTitleChange = (slideIndex: number, itemIndex: number, newTitle: string) => {
    if (!pptContent) return;
    const newSlides = [...pptContent.slides];
    newSlides[slideIndex].content[itemIndex].title = newTitle;
    setPptContent({ ...pptContent, slides: newSlides });
  };

  const handleSlideItemDescriptionChange = (slideIndex: number, itemIndex: number, newDesc: string) => {
    if (!pptContent) return;
    const newSlides = [...pptContent.slides];
    newSlides[slideIndex].content[itemIndex].description = newDesc;
    setPptContent({ ...pptContent, slides: newSlides });
  };

  return (
    <div className="min-h-screen bg-[#FFFDF8] py-12 px-4 sm:px-6 lg:px-8 font-sans relative">
      {/* History Toggle Button */}
      <button 
        onClick={() => setShowHistory(!showHistory)}
        className="fixed top-8 left-8 z-50 p-3 bg-white border border-gray-100 rounded-full shadow-lg hover:shadow-xl transition-all group"
        title="查看历史记录"
      >
        <History className={`w-6 h-6 ${showHistory ? 'text-[#E88E2E]' : 'text-gray-400 group-hover:text-[#E88E2E]'}`} />
      </button>

      {/* History Sidebar Overlay */}
      {showHistory && (
        <div 
          className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40 transition-opacity"
          onClick={() => setShowHistory(false)}
        />
      )}

      {/* History Sidebar */}
      <div className={`fixed top-0 left-0 h-full w-80 bg-white shadow-2xl z-50 transform transition-transform duration-300 ease-in-out ${showHistory ? 'translate-x-0' : '-translate-x-full'} border-r border-gray-100 flex flex-col`}>
        <div className="p-6 border-b border-gray-50 flex items-center justify-between">
          <h2 className="text-xl font-bold text-gray-800 flex items-center">
            <Clock className="w-5 h-5 mr-2 text-[#E88E2E]" />
            历史记录
          </h2>
          <button onClick={() => setShowHistory(false)} className="text-gray-400 hover:text-gray-600">
            <XCircle className="w-6 h-6" />
          </button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {history.length === 0 ? (
            <div className="text-center py-12">
              <History className="w-12 h-12 text-gray-100 mx-auto mb-4" />
              <p className="text-gray-400">暂无历史记录</p>
            </div>
          ) : (
            history.map((item) => (
              <div 
                key={item.id}
                onClick={() => handleSelectHistory(item)}
                className="group relative p-4 bg-gray-50 rounded-xl border border-transparent hover:border-[#FFD700] hover:bg-white transition-all cursor-pointer"
              >
                <div className="pr-8">
                  <h3 className="font-bold text-gray-800 text-sm line-clamp-2 mb-1 group-hover:text-[#E88E2E]">
                    {item.title}
                  </h3>
                  <p className="text-[10px] text-gray-400">
                    {new Date(item.timestamp).toLocaleString()}
                  </p>
                </div>
                <button 
                  onClick={(e) => deleteHistoryItem(e, item.id)}
                  className="absolute top-4 right-4 p-1 text-gray-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))
          )}
        </div>
      </div>

      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12 mt-8">
          <div className="inline-flex items-center justify-center px-4 py-1 rounded-full bg-orange-50 text-orange-600 text-sm font-medium mb-6 border border-orange-100">
            ✨ 基于大模型的原生 AI PPT 生成器
          </div>
          <h1 className="text-5xl font-extrabold tracking-tight text-[#E88E2E] mb-4 drop-shadow-sm">
            GenPPT · AI Slides
          </h1>
          <p className="text-xl text-gray-500">
            Vibe your slides like vibe coding
          </p>
        </div>

        {/* Main Input Card */}
        <div className="bg-white rounded-2xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-gray-100 overflow-hidden mb-8">
          {/* Fake Tabs */}
          <div className="flex border-b border-gray-100 px-6 pt-4 space-x-2">
            <div className="px-6 py-3 bg-[#FFD700] text-gray-900 font-semibold rounded-t-xl flex items-center shadow-sm">
              <Sparkles className="w-4 h-4 mr-2" />
              一句话生成
            </div>
            {/* Optional muted tabs for visual effect */}
            {/* <div className="px-6 py-3 text-gray-400 font-medium rounded-t-xl flex items-center">
               从大纲生成
            </div> */}
          </div>

          <div className="p-8">
            <p className="text-sm font-semibold text-[#E88E2E] mb-4 flex items-center">
              <span className="mr-2 text-lg">💡</span> 输入你的想法，AI 将为你生成完整的 PPT
            </p>
            
            {!isPolished ? (
              <div className="relative">
                <textarea
                  rows={5}
                  value={topic}
                  onChange={(e) => setTopic(e.target.value)}
                  className="block w-full rounded-xl border-0 py-4 px-5 text-gray-900 bg-gray-50 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-[#FFD700] text-lg resize-none outline-none transition-shadow"
                  placeholder="例如：生成一份关于 AI 发展史的演讲 PPT"
                />
                <div className="absolute bottom-4 right-4 flex space-x-3">
                  <button
                    onClick={handlePolish}
                    disabled={!topic || polishing}
                    className="inline-flex items-center px-6 py-2.5 border border-[#FFD700] text-sm font-bold rounded-lg text-gray-900 bg-white hover:bg-gray-50 focus:outline-none disabled:opacity-50 transition-colors"
                  >
                    {polishing && <Loader2 className="animate-spin -ml-1 mr-2 h-4 w-4" />}
                    润色主题
                  </button>
                  <button
                    onClick={handleGenerate}
                    disabled={!topic || loading}
                    className="inline-flex items-center px-8 py-2.5 border border-transparent text-sm font-bold rounded-lg shadow-sm text-gray-900 bg-[#FFD700] hover:bg-[#F6C800] focus:outline-none disabled:opacity-50 transition-colors"
                  >
                    {loading && <Loader2 className="animate-spin -ml-1 mr-2 h-4 w-4" />}
                    直接生成
                  </button>
                </div>
              </div>
            ) : (
              <div className="bg-orange-50 rounded-xl p-6 border border-orange-100">
                <div className="flex justify-between items-center mb-4">
                  <span className="text-sm font-bold text-orange-600 uppercase tracking-wider">润色后的主题建议</span>
                  <button 
                    onClick={() => setIsPolished(false)}
                    className="text-xs text-gray-400 hover:text-gray-600 underline"
                  >
                    重新输入
                  </button>
                </div>
                <textarea
                  rows={3}
                  value={polishedTopic}
                  onChange={(e) => setPolishedTopic(e.target.value)}
                  className="block w-full rounded-lg border-0 py-3 px-4 text-gray-900 bg-white shadow-sm focus:ring-2 focus:ring-[#FFD700] text-xl font-medium resize-none outline-none mb-6"
                />
                <div className="flex justify-end space-x-3">
                  {loading && (
                    <button
                      onClick={handleCancel}
                      className="inline-flex items-center px-4 py-2.5 border border-red-200 text-sm font-semibold rounded-lg text-red-600 bg-red-50 hover:bg-red-100 focus:outline-none transition-colors"
                    >
                      <XCircle className="w-4 h-4 mr-2" />
                      停止生成
                    </button>
                  )}
                  <button
                    onClick={handleGenerate}
                    disabled={loading}
                    className="inline-flex items-center px-10 py-3 border border-transparent text-base font-bold rounded-lg shadow-md text-gray-900 bg-[#FFD700] hover:bg-[#F6C800] focus:outline-none disabled:opacity-50 transition-all transform hover:scale-105"
                  >
                    {loading && <Loader2 className="animate-spin -ml-1 mr-2 h-5 w-5" />}
                    开始生成完整 PPT
                  </button>
                </div>
              </div>
            )}
            
            {/* API Key and Provider Selection */}
            <div className="mt-6 flex flex-col sm:flex-row items-center justify-between border-t border-gray-100 pt-4 gap-4">
              <div className="flex items-center w-full max-w-sm">
                 <select
                  value={provider}
                  onChange={(e) => setProvider(e.target.value)}
                  className="mr-3 block rounded-md border-0 py-1.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-200 focus:ring-2 focus:ring-inset focus:ring-[#FFD700] sm:text-sm sm:leading-6 outline-none bg-white"
                >
                  <option value="openai">OpenAI (GPT-4o)</option>
                  <option value="doubao">Doubao (Volcengine)</option>
                  <option value="qwen">Qwen (DashScope)</option>
                  <option value="gemini">Gemini (Google)</option>
                </select>
                <input
                  type="password"
                  id="apiKey"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                  className="block w-full rounded-md border-0 py-1.5 px-3 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-200 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-[#FFD700] sm:text-sm sm:leading-6 outline-none"
                  placeholder={`${provider} API Key (可选)`}
                />
              </div>
              <p className="text-xs text-gray-400">
                {/* 优先使用输入框中的 Key，留空则使用后端 .env 配置 */}
              </p>
            </div>

            {error && (
              <div className="mt-4 p-4 bg-red-50 text-red-700 rounded-md text-sm border border-red-100">
                {error}
              </div>
            )}
          </div>
        </div>

        {/* Content Section (Outline or Preview) */}
        {pptContent && (
          <div className="bg-white rounded-2xl shadow-[0_8px_30px_rgb(0,0,0,0.04)] border border-gray-100 overflow-hidden transition-all duration-500">
            {/* Fake Tabs for Outline / Preview */}
            <div className="flex border-b border-gray-100 px-6 pt-4 space-x-2 bg-gray-50/50">
              <button 
                onClick={() => setViewMode('outline')}
                className={`px-6 py-3 font-semibold rounded-t-xl flex items-center transition-colors ${viewMode === 'outline' ? 'bg-white text-[#E88E2E] shadow-sm border-t border-x border-gray-100' : 'text-gray-500 hover:text-gray-700'}`}
              >
                <LayoutList className="w-4 h-4 mr-2" />
                大纲编辑
              </button>
              <button 
                onClick={() => setViewMode('preview')}
                className={`px-6 py-3 font-semibold rounded-t-xl flex items-center transition-colors ${viewMode === 'preview' ? 'bg-white text-[#E88E2E] shadow-sm border-t border-x border-gray-100' : 'text-gray-500 hover:text-gray-700'}`}
              >
                <Sparkles className="w-4 h-4 mr-2" />
                效果预览
              </button>
            </div>

            <div className="p-8">
              {viewMode === 'outline' ? (
                <div className="flex flex-col space-y-6">
                  {/* AI Modify Input */}
                  <div className="flex items-center space-x-3 bg-[#FFFDF8] p-4 rounded-xl border border-[#FFD700]/30 shadow-sm">
                    <Sparkles className="w-5 h-5 text-[#E88E2E]" />
                    <input
                      type="text"
                      value={modifyInstruction}
                      onChange={(e) => setModifyInstruction(e.target.value)}
                      placeholder="告诉 AI你想怎么修改大纲，例如：增加一页关于商业模式的内容..."
                      className="flex-1 bg-transparent border-none focus:ring-0 text-gray-800 placeholder:text-gray-400 outline-none"
                      onKeyDown={(e) => e.key === 'Enter' && handleModifyOutline()}
                    />
                    <button
                      onClick={handleModifyOutline}
                      disabled={!modifyInstruction || modifying}
                      className="p-2 bg-[#FFD700] text-gray-900 rounded-lg hover:bg-[#F6C800] disabled:opacity-50 transition-colors"
                    >
                      {modifying ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
                    </button>
                  </div>

                  {/* Outline Cards */}
                  <div className="space-y-4 max-h-[600px] overflow-y-auto pr-2 pb-4">
                    {pptContent.slides.map((slide, index) => (
                      <div key={index} className="bg-white border border-gray-100 shadow-sm rounded-xl p-5 hover:shadow-md transition-shadow relative group">
                        <div className="absolute left-0 top-0 bottom-0 w-1 bg-[#E88E2E] rounded-l-xl opacity-50 group-hover:opacity-100 transition-opacity"></div>
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center flex-1">
                            <span className="text-xs font-bold text-gray-400 bg-gray-100 px-2 py-1 rounded mr-3">
                              第 {index + 1} 页
                            </span>
                            <input
                              type="text"
                              value={slide.page_title}
                              onChange={(e) => handleSlideTitleChange(index, e.target.value)}
                              className="text-lg font-bold text-gray-800 border-b-2 border-transparent hover:border-gray-200 focus:border-[#E88E2E] focus:outline-none bg-transparent w-full transition-all"
                            />
                          </div>
                        </div>
                        <div className="pl-12 space-y-4">
                          {slide.content.map((c, cIdx) => (
                            <div key={cIdx} className="flex flex-col space-y-1">
                              <div className="flex items-center">
                                <span className="text-gray-400 mr-2 text-xs">•</span>
                                <input
                                  type="text"
                                  value={c.title}
                                  onChange={(e) => handleSlideItemTitleChange(index, cIdx, e.target.value)}
                                  className="text-sm font-semibold text-gray-700 border-b border-transparent hover:border-gray-100 focus:border-[#FFD700] focus:outline-none bg-transparent w-full transition-colors"
                                />
                              </div>
                              <textarea
                                value={c.description}
                                onChange={(e) => handleSlideItemDescriptionChange(index, cIdx, e.target.value)}
                                rows={2}
                                className="text-sm text-gray-500 pl-3 border-none hover:bg-gray-50 focus:bg-gray-50 focus:ring-0 focus:outline-none bg-transparent w-full resize-none rounded transition-colors"
                              />
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                  
                  <div className="flex justify-end pt-4 border-t border-gray-100">
                    <button
                      onClick={() => setViewMode('preview')}
                      className="inline-flex items-center px-8 py-3 border border-transparent text-base font-bold rounded-lg shadow-sm text-gray-900 bg-[#FFD700] hover:bg-[#F6C800] focus:outline-none transition-all transform hover:scale-105"
                    >
                      完成修改，生成 PPT
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                      <span className="bg-[#FFD700] w-1.5 h-6 rounded-full mr-3"></span>
                      最终效果预览
                    </h2>
                    <div className="flex items-center space-x-3">
                      <button
                        onClick={handlePreviewHtml}
                        disabled={generatingHtml}
                        className="inline-flex items-center px-4 py-2.5 border border-gray-300 text-sm font-semibold rounded-lg text-gray-700 bg-white hover:bg-gray-50 focus:outline-none transition-colors"
                        title="在新窗口打开演示"
                      >
                        {generatingHtml ? <Loader2 className="animate-spin h-4 w-4" /> : <Sparkles className="h-4 w-4" />}
                        <span className="ml-2">网页全屏播放</span>
                      </button>
                      <button
                        onClick={handleDownloadHtml}
                        disabled={generatingHtml}
                        className="inline-flex items-center px-4 py-2.5 border border-[#4CAF50] text-sm font-bold rounded-lg shadow-sm text-[#4CAF50] bg-white hover:bg-[#f0f9f0] focus:outline-none transition-colors"
                      >
                        {generatingHtml ? <Loader2 className="animate-spin h-4 w-4" /> : <FileDown className="h-4 w-4" />}
                        <span className="ml-2">下载 HTML</span>
                      </button>
                      <button
                        onClick={handleDownload}
                        disabled={generatingFile}
                        className="inline-flex items-center px-4 py-2.5 border border-transparent text-sm font-bold rounded-lg shadow-sm text-white bg-[#4CAF50] hover:bg-[#45a049] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#4CAF50] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      >
                        {generatingFile ? <Loader2 className="animate-spin h-4 w-4" /> : <FileDown className="h-4 w-4" />}
                        <span className="ml-2">下载 PPTX</span>
                      </button>
                    </div>
                  </div>
                  
                  <div className="w-full bg-gray-50 p-2 rounded-xl border border-gray-100" key={JSON.stringify(pptContent.slides)}>
                     <Preview 
                      slides={pptContent.slides} 
                      title={pptContent.title} 
                      themeColor={pptContent.theme_color}
                      accentColor={pptContent.accent_color}
                     />
                  </div>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
