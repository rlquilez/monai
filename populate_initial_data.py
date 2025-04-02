from database import SessionLocal, engine
from models import Base, Job, Rule, RuleGroup
from datetime import datetime
import uuid

# Criar as tabelas
Base.metadata.create_all(bind=engine)

# Função para criar o job inicial
def create_initial_job(db):
    job = Job(
        id="476ff69a79039e89d7044ebb9959fede2cc2468744b5c3ea7adda58423f4aebd",
        job_name="Envio Diário Base Full - Banco Joelma",
        job_filename="BASEDIARIA.csv",
        description="Job para envio diário da base full do Banco Joelma",
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    db.add(job)
    db.commit()
    return job

# Função para criar todas as regras
def create_all_rules(db):
    rules = [
        # Regras Matemáticas Básicas
        Rule(
            id=uuid.uuid4(),
            name="Validação de Média com Min e Max",
            description="Verifica se o valor médio está dentro do intervalo definido pelos valores mínimo e máximo",
            rule_text="Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'avg', juntamente com 'min' e 'max', o valor de 'avg' deve estar dentro do intervalo definido pelos valores de 'min' e 'max'.",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        Rule(
            id=uuid.uuid4(),
            name="Validação de Média com Min e Max (mean)",
            description="Verifica se o valor mean está dentro do intervalo definido pelos valores mínimo e máximo",
            rule_text="Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'mean', juntamente com 'min' e 'max', o valor de 'mean' deve estar dentro do intervalo definido pelos valores de 'min' e 'max'.",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        Rule(
            id=uuid.uuid4(),
            name="Validação de Máximo",
            description="Verifica se o valor máximo é maior que o valor mínimo",
            rule_text="Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'max', o valor de 'max' deve ser maior que o valor de 'min'.",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        Rule(
            id=uuid.uuid4(),
            name="Validação de Desvio Padrão",
            description="Verifica se o desvio padrão é menor que a diferença entre máximo e mínimo",
            rule_text="Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'std', juntamente com 'min' e 'max', o valor de 'std' deve ser menor que a diferença entre os valores de 'max' e 'min'.",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        Rule(
            id=uuid.uuid4(),
            name="Validação de Desvio Padrão (stdev)",
            description="Verifica se o desvio padrão (stdev) é menor que a diferença entre máximo e mínimo",
            rule_text="Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'stdev', juntamente com 'min' e 'max', o valor de 'stdev' deve ser menor que a diferença entre os valores de 'max' e 'min'.",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        # Regras de Contagem e Soma
        Rule(
            id=uuid.uuid4(),
            name="Validação de Contagem",
            description="Verifica se o valor de contagem é maior que zero",
            rule_text="Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'count', o valor de 'count' deve ser maior que zero.",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        Rule(
            id=uuid.uuid4(),
            name="Validação de Soma",
            description="Verifica se o valor da soma é maior que zero",
            rule_text="Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'sum', o valor de 'sum' deve ser maior que zero.",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        # Regras de Medidas de Tendência Central
        Rule(
            id=uuid.uuid4(),
            name="Validação de Mediana",
            description="Verifica se a mediana está entre os valores mínimo e máximo",
            rule_text="Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'median', o valor de 'median' deve estar entre os valores de 'min' e 'max'.",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        Rule(
            id=uuid.uuid4(),
            name="Validação de Moda",
            description="Verifica se a moda está entre os valores mínimo e máximo",
            rule_text="Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'mode', o valor de 'mode' deve estar entre os valores de 'min' e 'max'.",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        # Regras de Medidas de Dispersão
        Rule(
            id=uuid.uuid4(),
            name="Validação de Variância",
            description="Verifica se a variância é maior que zero",
            rule_text="Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'variance', o valor de 'variance' deve ser maior que zero.",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        Rule(
            id=uuid.uuid4(),
            name="Validação de Assimetria",
            description="Verifica se a assimetria é maior que zero",
            rule_text="Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'skewness', o valor de 'skewness' deve ser maior que zero.",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        Rule(
            id=uuid.uuid4(),
            name="Validação de Curtose",
            description="Verifica se a curtose é maior que zero",
            rule_text="Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'kurtosis', o valor de 'kurtosis' deve ser maior que zero.",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        Rule(
            id=uuid.uuid4(),
            name="Validação de Amplitude",
            description="Verifica se a amplitude é maior que zero",
            rule_text="Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'range', o valor de 'range' deve ser maior que zero.",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        Rule(
            id=uuid.uuid4(),
            name="Validação de IQR",
            description="Verifica se o IQR é maior que zero",
            rule_text="Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'iqr', o valor de 'iqr' deve ser maior que zero.",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        Rule(
            id=uuid.uuid4(),
            name="Validação de MAD",
            description="Verifica se o MAD é maior que zero",
            rule_text="Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'mad', o valor de 'mad' deve ser maior que zero.",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        Rule(
            id=uuid.uuid4(),
            name="Validação de CV",
            description="Verifica se o coeficiente de variação é maior que zero",
            rule_text="Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'cv', o valor de 'cv' deve ser maior que zero.",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        # Regras de Análise Estatística
        Rule(
            id=uuid.uuid4(),
            name="Validação de Z-Score",
            description="Verifica se o Z-Score é maior que zero",
            rule_text="Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'z_score', o valor de 'z_score' deve ser maior que zero.",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        Rule(
            id=uuid.uuid4(),
            name="Validação de P-Valor",
            description="Verifica se o P-Valor é maior que zero",
            rule_text="Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'p_value', o valor de 'p_value' deve ser maior que zero.",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        Rule(
            id=uuid.uuid4(),
            name="Validação de Intervalo de Confiança",
            description="Verifica se o intervalo de confiança é maior que zero",
            rule_text="Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'confidence_interval', o valor de 'confidence_interval' deve ser maior que zero.",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        Rule(
            id=uuid.uuid4(),
            name="Validação de Limite Superior",
            description="Verifica se o limite superior é maior que zero",
            rule_text="Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'upper_bound', o valor de 'upper_bound' deve ser maior que zero.",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        Rule(
            id=uuid.uuid4(),
            name="Validação de Limite Inferior",
            description="Verifica se o limite inferior é maior que zero",
            rule_text="Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'lower_bound', o valor de 'lower_bound' deve ser maior que zero.",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        Rule(
            id=uuid.uuid4(),
            name="Validação de Outliers",
            description="Verifica se o número de outliers é maior que zero",
            rule_text="Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'outliers', o valor de 'outliers' deve ser maior que zero.",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        # Regras de Percentis
        Rule(
            id=uuid.uuid4(),
            name="Validação de Percentis",
            description="Verifica se os percentis são maiores que zero",
            rule_text="Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'percentiles', o valor de 'percentiles' deve ser maior que zero.",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        Rule(
            id=uuid.uuid4(),
            name="Validação de Decis",
            description="Verifica se os decis são maiores que zero",
            rule_text="Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'deciles', o valor de 'deciles' deve ser maior que zero.",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        Rule(
            id=uuid.uuid4(),
            name="Validação de Quartis",
            description="Verifica se os quartis são maiores que zero",
            rule_text="Ao aplicar esta regra, considere a avaliação do último dado recebido e não compare com o histórico. Se houver valores para 'quartiles', o valor de 'quartiles' deve ser maior que zero.",
            is_active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    ]
    
    for rule in rules:
        db.add(rule)
    db.commit()
    return rules

# Função para criar os grupos de regras
def create_rule_groups(db, rules):
    # Grupo de Validações Matemáticas Básicas
    math_rules = [rule for rule in rules if any(keyword in rule.rule_text.lower() 
                                              for keyword in ['avg', 'mean', 'max', 'min', 'std', 'stdev'])]
    math_group = RuleGroup(
        id=uuid.uuid4(),
        name="Validações Matemáticas Básicas",
        description="Grupo de regras para validações matemáticas básicas como média, máximo, mínimo e desvio padrão",
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    math_group.rules = math_rules
    db.add(math_group)
    
    # Grupo de Validações de Contagem e Soma
    count_sum_rules = [rule for rule in rules if any(keyword in rule.rule_text.lower() 
                                                   for keyword in ['count', 'sum'])]
    count_sum_group = RuleGroup(
        id=uuid.uuid4(),
        name="Validações de Contagem e Soma",
        description="Grupo de regras para validações de contagem e soma",
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    count_sum_group.rules = count_sum_rules
    db.add(count_sum_group)
    
    # Grupo de Validações de Medidas de Tendência Central
    central_tendency_rules = [rule for rule in rules if any(keyword in rule.rule_text.lower() 
                                                          for keyword in ['median', 'mode'])]
    central_tendency_group = RuleGroup(
        id=uuid.uuid4(),
        name="Validações de Medidas de Tendência Central",
        description="Grupo de regras para validações de medidas de tendência central",
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    central_tendency_group.rules = central_tendency_rules
    db.add(central_tendency_group)
    
    # Grupo de Validações de Medidas de Dispersão
    dispersion_rules = [rule for rule in rules if any(keyword in rule.rule_text.lower() 
                                                    for keyword in ['variance', 'skewness', 'kurtosis', 'range', 'iqr', 'mad', 'cv'])]
    dispersion_group = RuleGroup(
        id=uuid.uuid4(),
        name="Validações de Medidas de Dispersão",
        description="Grupo de regras para validações de medidas de dispersão",
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    dispersion_group.rules = dispersion_rules
    db.add(dispersion_group)
    
    # Grupo de Validações de Análise Estatística
    statistical_rules = [rule for rule in rules if any(keyword in rule.rule_text.lower() 
                                                     for keyword in ['z_score', 'p_value', 'confidence_interval', 'upper_bound', 'lower_bound', 'outliers'])]
    statistical_group = RuleGroup(
        id=uuid.uuid4(),
        name="Validações de Análise Estatística",
        description="Grupo de regras para validações de análise estatística",
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    statistical_group.rules = statistical_rules
    db.add(statistical_group)
    
    # Grupo de Validações de Percentis
    percentile_rules = [rule for rule in rules if any(keyword in rule.rule_text.lower() 
                                                    for keyword in ['percentiles', 'deciles', 'quartiles'])]
    percentile_group = RuleGroup(
        id=uuid.uuid4(),
        name="Validações de Percentis",
        description="Grupo de regras para validações de percentis",
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    percentile_group.rules = percentile_rules
    db.add(percentile_group)
    
    db.commit()
    return [math_group, count_sum_group, central_tendency_group, dispersion_group, statistical_group, percentile_group]

# Função principal para popular o banco de dados
def populate_database():
    db = SessionLocal()
    try:
        # Criar o job inicial
        job = create_initial_job(db)
        print("Job inicial criado com sucesso!")

        # Criar todas as regras
        rules = create_all_rules(db)
        print("Regras criadas com sucesso!")

        # Criar os grupos de regras
        groups = create_rule_groups(db, rules)
        print("Grupos de regras criados com sucesso!")

        # Associar apenas o grupo de Validações Matemáticas Básicas ao job
        math_group = next(group for group in groups if group.name == "Validações Matemáticas Básicas")
        job.rule_groups.append(math_group)
        db.commit()
        print("Grupo de Validações Matemáticas Básicas associado ao job com sucesso!")

    except Exception as e:
        print(f"Erro ao popular o banco de dados: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    populate_database() 