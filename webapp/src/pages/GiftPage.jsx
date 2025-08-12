import React, {useEffect, useState} from "react";
import {useParams} from "react-router-dom";
import LazyImage from "../components/LazyImage";

export default function GiftPage(){
  const {slug} = useParams();
  const [payload, setPayload] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);

  useEffect(()=>{
    fetch(`/api/gifts/${slug}`)
      .then(r=>{
        if(!r.ok) throw new Error("Not found");
        return r.json();
      })
      .then(data=>{
        setPayload(data);
      })
      .catch(err=>{
        console.error(err);
        setPayload(null);
      })
      .finally(()=>setLoading(false));
  }, [slug]);

  if(loading) return <div className="min-h-screen bg-[#0d1117] text-white flex items-center justify-center">Загрузка...</div>;
  if(!payload) return <div className="min-h-screen bg-[#0d1117] text-white flex items-center justify-center">Товар не найден</div>;

  const percent = (n) => (n != null ? (n/10).toFixed(1) + "%" : "—");

  return (
    <div className="min-h-screen bg-[#0d1117] text-white p-4">
      <header className="flex items-center justify-between max-w-3xl mx-auto">
        <h1 className="text-xl font-semibold">{payload.title}</h1>
        <button className="px-3 py-1 border rounded">Connect Wallet</button>
      </header>

      <main className="max-w-3xl mx-auto mt-6">
        <div className="bg-[#0b0f13] rounded-lg p-4 md:p-8">
          <div className="flex flex-col md:flex-row items-center gap-6">
            <div className="w-full md:w-1/2">
              <LazyImage src={payload.image_url} alt={payload.title} />
            </div>
            <div className="w-full md:w-1/2">
              <h2 className="text-lg font-medium mb-2">{payload.model_name}</h2>
              <div className="mb-4">
                <div>Model: {payload.model_name} — {percent(payload.model_rarity_per_mille)}</div>
                <div>Symbol: {payload.symbol_name} — {percent(payload.symbol_rarity_per_mille)}</div>
                <div>Backdrop: {payload.backdrop_color} — {percent(payload.backdrop_rarity_per_mille)}</div>
              </div>
              <button onClick={()=>setShowModal(true)} className="bg-blue-600 px-4 py-2 rounded text-white">
                Buy — {payload.price}
              </button>
            </div>
          </div>
        </div>
      </main>

      {showModal && (
        <div className="fixed inset-0 flex items-center justify-center z-50">
          <div className="absolute inset-0 bg-black/60" onClick={()=>setShowModal(false)}></div>
          <div className="bg-white text-black rounded-lg p-8 z-10 transform transition-all animate-fade">
            <h3 className="text-2xl mb-4">Спасибо</h3>
            <p>Транзакция инициирована (имитация)</p>
            <button className="mt-4 px-4 py-2 bg-[#0d1117] text-white rounded" onClick={()=>setShowModal(false)}>Закрыть</button>
          </div>
        </div>
      )}
      <style>{`
        @keyframes fade { from { opacity: 0; transform: scale(.95);} to {opacity:1; transform:scale(1);} }
        .animate-fade { animation: fade .25s ease-out; }
      `}</style>
    </div>
  );
}
