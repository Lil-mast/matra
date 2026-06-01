import { openDB } from 'idb';


let dbPromise: Promise<any> | null = null;

export function initDB() {
  if (!dbPromise) {
    dbPromise = openDB('matra-offline-db', 1, {
      upgrade(db) {
        const store = db.createObjectStore('assessments', {
          keyPath: 'id',
          autoIncrement: true,
        });
        store.createIndex('synced', 'synced');
      },
    });
  }
  return dbPromise;
}

// Basic client-side triage logic (mimics backend for offline use)
export function evaluateRiskOffline(data: any): { risk_level: 'high' | 'intermediate' | 'low', recommended_action: string } {
    let score = 0;
    
    // Danger signs (Immediate high risk)
    if (data.convulsions || data.bleeding == 2 || data.systolic_bp >= 160 || data.diastolic_bp >= 110) {
        return { risk_level: 'high', recommended_action: 'IMMEDIATE REFERRAL TO HOSPITAL' };
    }
    
    // Intermediate signs
    if (data.fever) score += 2;
    if (data.reduced_fetal_movement) score += 2;
    if (data.bleeding == 1) score += 2;
    if (data.anemia) score += 1;
    if (data.systolic_bp >= 140 || data.diastolic_bp >= 90) score += 2;
    if (data.pulse > 100) score += 1;
    
    if (score >= 3) {
        return { risk_level: 'high', recommended_action: 'REFER TO HOSPITAL' };
    } else if (score >= 1) {
        return { risk_level: 'intermediate', recommended_action: 'OBSERVE AND REASSESS IN 4 HOURS' };
    }
    
    return { risk_level: 'low', recommended_action: 'ROUTINE ANTENATAL CARE' };
}

export async function saveAssessment(data: any) {
  const db = await initDB();
  
  // Calculate offline risk
  const offlineEval = evaluateRiskOffline(data);
  const record = {
      ...data,
      ...offlineEval,
      timestamp: Date.now(),
      synced: false
  };
  
  const id = await db.add('assessments', record);
  return { id, ...offlineEval };
}

export async function getOfflineAssessments() {
  const db = await initDB();
  return db.getAllFromIndex('assessments', 'synced', false);
}

export async function getAllAssessments() {
  const db = await initDB();
  return db.getAll('assessments');
}

export async function markAsSynced(ids: number[]) {
  const db = await initDB();
  const tx = db.transaction('assessments', 'readwrite');
  for (const id of ids) {
    const record = await tx.store.get(id);
    if (record) {
      record.synced = true;
      await tx.store.put(record);
    }
  }
  await tx.done;
}
