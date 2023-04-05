package com.capstone.aiconan.domain;

import lombok.AccessLevel;
import lombok.Builder;
import lombok.NoArgsConstructor;

import javax.persistence.*;

@Entity
@Table(name = "abnormal_packets")
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class Abnormal {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne
    @JoinColumn(name = "attack_types_id")
    private AttackType attackType;

    @Builder
    private Abnormal(AttackType attackType) {
        this.attackType = attackType;
    }
}
