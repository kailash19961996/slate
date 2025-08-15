// src/functions/justlend_handlers.jsx
// Map backend function_calls → widget state + chat messages (with error surfacing)

export async function handleJustLendListMarkets({ fc, setMessages, setCurrentWidget, setJustLendData }) {
    console.log('📈 [JL] list_markets payload:', fc);
    const data = fc?.result || {};
    if (data?.error) {
      console.error('❌ [JL] list_markets error:', data.error);
      setMessages(prev => [...prev, {
        id: Date.now()+Math.random(),
        text: `❌ JustLend error: ${data.error}`,
        sender: 'ai', timestamp: new Date()
      }]);
      setCurrentWidget('idle');
      return;
    }
    setJustLendData({ view: 'list', payload: data });
    setCurrentWidget('justlend');
    const count = data?.count ?? (data?.markets?.length || 0);
    setMessages(prev => [...prev, { id: Date.now()+Math.random(), text: `📊 JustLend: found ${count} markets.`, sender: 'ai', timestamp: new Date() }]);
  }
  
  export async function handleJustLendMarketDetail({ fc, setMessages, setCurrentWidget, setJustLendData }) {
    console.log('🔍 [JL] market_detail payload:', fc);
    const data = fc?.result || {};
    if (data?.error) {
      console.error('❌ [JL] market_detail error:', data.error);
      setMessages(prev => [...prev, { id: Date.now()+Math.random(), text: `❌ JustLend error: ${data.error}`, sender: 'ai', timestamp: new Date() }]);
      setCurrentWidget('idle');
      return;
    }
    setJustLendData({ view: 'detail', payload: data });
    setCurrentWidget('justlend');
    const sym = data?.market?.symbol || 'unknown';
    setMessages(prev => [...prev, { id: Date.now()+Math.random(), text: `ℹ️ JustLend: details for ${sym}.`, sender: 'ai', timestamp: new Date() }]);
  }
  
  export async function handleJustLendUserPosition({ fc, setMessages, setCurrentWidget, setJustLendData }) {
    console.log('👤 [JL] user_position payload:', fc);
    const data = fc?.result || {};
    if (data?.error) {
      console.error('❌ [JL] user_position error:', data.error);
      setMessages(prev => [...prev, { id: Date.now()+Math.random(), text: `❌ JustLend error: ${data.error}`, sender: 'ai', timestamp: new Date() }]);
      setCurrentWidget('idle');
      return;
    }
    setJustLendData({ view: 'user', payload: data });
    setCurrentWidget('justlend');
    const addr = data?.address ? `${data.address.slice(0,6)}...${data.address.slice(-4)}` : 'your address';
    setMessages(prev => [...prev, { id: Date.now()+Math.random(), text: `🧾 JustLend: showing position for ${addr}.`, sender: 'ai', timestamp: new Date() }]);
  }
  