export function Header() {
  return (
    <header className="h-16 bg-white border-b border-gray-100 flex items-center justify-between px-8 shrink-0 sticky top-0 z-50">
      <div className="flex items-center gap-6">
        <div className="flex flex-col leading-tight">
          <span className="font-extrabold text-lg tracking-tighter text-gray-900">
            STOCKY
          </span>
        </div>
        <div className="h-4 w-px bg-gray-200"></div>
        <span className="text-xs uppercase font-medium text-gray-400 tracking-widest">
          Warehouse overview
        </span>
      </div>

      <div className="flex items-center gap-8">
        <div className="hidden md:flex items-center gap-2">
        </div>

        <div className="flex items-center gap-6 border-l border-gray-100 pl-8">
          <button className="relative inline-flex items-center gap-2 rounded-full border border-gray-200 bg-white px-3 py-1.5 text-xs font-semibold uppercase tracking-widest text-gray-500 transition-colors hover:border-gray-300 hover:text-gray-900">
            Alerts
            <span className="inline-flex h-2.5 w-2.5 rounded-full bg-red-500 shadow-[0_0_0_3px_rgba(239,68,68,0.12)]"></span>
          </button>
          <div className="h-8 w-8 bg-gray-50 rounded-full flex items-center justify-center cursor-pointer border border-gray-200 hover:bg-gray-100 transition-colors">
            <span className="text-xs font-bold text-gray-900">A</span>
          </div>
        </div>
      </div>
    </header>
  );
}
