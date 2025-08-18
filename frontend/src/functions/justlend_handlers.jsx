// src/functions/justlend_handlers.jsx

// ------------------------------------------------------------
// Wallet tools used by justlend_handlers.jsx
// 1) handleJustLendListMarkets()
// 2) handleJustLendMarketDetail()
// 3) handleJustLendUserPosition()
// ------------------------------------------------------------

export async function handleJustLendListMarkets({ fc, setCurrentWidget, setJustLendData }) {
    console.log('📈 [JL] list_markets payload:', fc);
    
    setCurrentWidget('thinking');
    
    const data = fc?.result || fc || {};
    
    if (data?.error) {
      console.error('❌ [JL] list_markets error:', data.error);
      setCurrentWidget('idle');
      return;
    }
    
    console.log('📈 [JL] Processing markets data:', data);
    setJustLendData({ view: 'list', payload: data });
    setCurrentWidget('justlend');
  }
  
  export async function handleJustLendMarketDetail({ fc, setCurrentWidget, setJustLendData }) {
    console.log('🔍 [JL] market_detail payload:', fc);
    
    setCurrentWidget('thinking');
    
    const data = fc?.result || {};
    if (data?.error) {
      console.error('❌ [JL] market_detail error:', data.error);
      setCurrentWidget('idle');
      return;
    }
    setJustLendData({ view: 'detail', payload: data });
    setCurrentWidget('justlend');
  }
  
  export async function handleJustLendUserPosition({ fc, setCurrentWidget, setJustLendData }) {
    console.log('👤 [JL] user_position payload:', fc);
    
    setCurrentWidget('thinking');
    
    const data = fc?.result || {};
    if (data?.error) {
      console.error('❌ [JL] user_position error:', data.error);
      setCurrentWidget('idle');
      return;
    }
    setJustLendData({ view: 'user', payload: data });
    setCurrentWidget('justlend');
  }
  