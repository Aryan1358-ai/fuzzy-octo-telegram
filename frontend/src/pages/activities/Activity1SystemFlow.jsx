/**
 * Activity 1: System Flow Arrangement
 * Drag 6 system blocks into the correct order of a request lifecycle.
 * Tracks: placement_order (chronological), final_positions
 */
import { useState, useRef, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { useActivitySubmit } from '../../api/useActivitySubmit';
import './Activities.css';

const INITIAL_BLOCKS = [
  { id: 'ml-model', label: 'ML Model', icon: '🤖' },
  { id: 'ui-response', label: 'UI Response', icon: '🖥️' },
  { id: 'api-gateway', label: 'API Gateway', icon: '🌐' },
  { id: 'database', label: 'Database', icon: '🗄️' },
  { id: 'user-request', label: 'User Request', icon: '👤' },
  { id: 'app-server', label: 'Application Server', icon: '⚙️' },
];

function SortableBlock({ id, label, icon }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`sortable-item ${isDragging ? 'dragging' : ''}`}
      {...attributes}
      {...listeners}
    >
      <span className="drag-handle">⠿</span>
      <span className="item-icon">{icon}</span>
      <div className="item-content">
        <strong>{label}</strong>
      </div>
    </div>
  );
}

export default function Activity1SystemFlow({ activityNumber, title }) {
  const [blocks, setBlocks] = useState(() =>
    [...INITIAL_BLOCKS].sort(() => Math.random() - 0.5)
  );
  const placementOrder = useRef([]);
  const startTime = useRef(Date.now());
  const { submit, submitting, submitted, error } = useActivitySubmit(activityNumber);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  );

  const handleDragEnd = useCallback((event) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;

    setBlocks((prev) => {
      const oldIndex = prev.findIndex((b) => b.id === active.id);
      const newIndex = prev.findIndex((b) => b.id === over.id);
      const newOrder = arrayMove(prev, oldIndex, newIndex);

      // Track the move
      placementOrder.current.push({
        label: prev[oldIndex].label,
        from: oldIndex,
        to: newIndex,
        timestamp: Date.now(),
      });

      return newOrder;
    });
  }, []);

  const handleSubmit = () => {
    submit({
      response_data: {
        placement_order: placementOrder.current,
        final_positions: blocks.map((b) => ({ label: b.label })),
      },
      duration_ms: Date.now() - startTime.current,
    });
  };

  return (
    <motion.div
      className="activity-page"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.4 }}
    >
      <div className="container">
        <div className="activity-header">
          <span className="activity-badge">Activity {activityNumber} of 6</span>
          <h2>{title}</h2>
          <p>
            A user sends a request to your app. Drag the components below into the
            order you think a request flows through the system.
          </p>
        </div>

        <div className="activity-content">
          <DndContext
            sensors={sensors}
            collisionDetection={closestCenter}
            onDragEnd={handleDragEnd}
          >
            <SortableContext
              items={blocks.map((b) => b.id)}
              strategy={verticalListSortingStrategy}
            >
              <div className="flex flex-col gap-4">
                {blocks.map((block, index) => (
                  <div key={block.id} className="flex items-center gap-4">
                    <span
                      style={{
                        color: 'var(--color-text-muted)',
                        fontSize: 'var(--font-size-sm)',
                        minWidth: '28px',
                        textAlign: 'right',
                      }}
                    >
                      {index + 1}.
                    </span>
                    <SortableBlock {...block} />
                  </div>
                ))}
              </div>
            </SortableContext>
          </DndContext>
        </div>

        <div className="activity-footer">
          {error && <p style={{ color: 'var(--color-error)', marginBottom: 'var(--space-3)', textAlign: 'center' }}>{error}</p>}
          <motion.button
            className="btn btn-primary btn-lg"
            onClick={handleSubmit}
            disabled={submitting || submitted}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            {submitted ? '✓ Submitted!' : submitting ? 'Submitting…' : 'Lock In Order →'}
          </motion.button>
        </div>
      </div>
    </motion.div>
  );
}
